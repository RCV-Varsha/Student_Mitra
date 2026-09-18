"""Repeatable Should Have regression cases; provider responses are fixtures, not live AI."""
import json
from io import BytesIO
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from reportlab.pdfgen.canvas import Canvas
from . import tests as fixtures
from .models import *
from .ai import generate, TutorOutput, stream_callback, AIError
from .learning import retrieve, tutor
from .providers import provider_for
from .insights import enqueue_insights, run_insight_job
from .documents import extract_document
from .jobs import claim_job, process_job

@override_settings(SECURE_SSL_REDIRECT=False)
class ShouldHaveTests(TestCase):
    setUp = fixtures.LearningTests.setUp
    question = fixtures.LearningTests.question
    def test_cache_hit_isolation_and_status_invalidation(self):
        self.assertEqual(retrieve(self.p,'photosynthesis')[0].id,self.chunk.id)
        with patch('study.learning._retrieve',side_effect=AssertionError('cache miss')):
            self.assertEqual(retrieve(self.p,'photosynthesis')[0].id,self.chunk.id)
        self.assertEqual(retrieve(self.p2,'photosynthesis'),[])
        self.m.status='failed';self.m.save()
        self.assertEqual(retrieve(self.p,'photosynthesis'),[])
    def test_poisoned_cache_cannot_expose_other_project(self):
        retrieve(self.p,'photosynthesis')
        cache=RetrievalCache.objects.get(project=self.p)
        foreign=Material.objects.create(project=self.foreign,name='private',digest='private',status='ready')
        secret=Chunk.objects.create(material=foreign,page=1,ordinal=0,text='Secret photosynthesis data')
        cache.chunk_ids=[secret.id];cache.save()
        self.assertEqual(retrieve(self.p,'photosynthesis')[0].id,self.chunk.id)
    def test_continuity_is_persistent_and_bounded(self):
        for i in range(22): tutor(self.user,self.p,f'Unsupported football result {i}',str(i))
        self.p.refresh_from_db();memory=self.p.context['continuity']
        self.assertEqual(memory['turn_count'],22);self.assertEqual(len(memory['recent_questions']),8)
        self.assertNotIn('continuity',self.p2.context)
    def test_insight_jobs_deduplicate_and_persist(self):
        q=self.question();Assessment.objects.create(question=q,answer='x',score=.2,feedback='Review light conversion',missing=['Energy conversion'],before=.5,after=.4)
        job=enqueue_insights(self.p,'assessment:1')
        self.assertEqual(enqueue_insights(self.p,'assessment:1').id,job.id)
        self.assertTrue(run_insight_job());job.refresh_from_db();self.p.refresh_from_db()
        self.assertEqual(job.status,'ready');self.assertEqual(self.p.context['insights']['recent_score'],.2)
        self.assertEqual(self.p.context['insights']['recurring_gaps'][0]['name'],'Energy conversion')
        self.assertFalse(run_insight_job())
    def test_insight_retry_and_ownership(self):
        job=enqueue_insights(self.p,'broken')
        with patch('study.insights.Assessment.objects.filter',side_effect=RuntimeError('private traceback')):run_insight_job()
        job.refresh_from_db();self.assertEqual(job.status,'queued');self.assertNotIn('private',job.error)
        self.assertGreater(job.available,timezone.now())
        self.assertEqual(self.client.post(f'/api/projects/{self.foreign.id}/insights/').status_code,404)
    def test_provider_adapters_have_equivalent_outputs(self):
        g=provider_for('gemini');o=provider_for('openai')
        self.assertEqual(g.parse({'candidates':[{'content':{'parts':[{'text':'hello'}]}}],'usageMetadata':{'promptTokenCount':3,'candidatesTokenCount':4}}),('hello',3,4))
        self.assertEqual(o.parse({'choices':[{'delta':{'content':'hello'}}],'usage':{'prompt_tokens':3,'completion_tokens':4}},True),('hello',3,4))
        for provider in [g,o]:
            url,headers,body=provider.request('test-secret','system',TutorOutput,{},True)
            self.assertNotIn('test-secret',url);self.assertNotIn('test-secret',json.dumps(body))
        with self.assertRaises(ValueError):provider_for('unrestricted')
    @override_settings(AI_PROVIDER='gemini',AI_MODEL='fixture-model')
    @patch.dict('os.environ',{'GEMINI_API_KEY':'fixture-key'})
    def test_streamed_output_validates_and_traces(self):
        output={'answer':'Plants convert light energy into chemical energy.','supported':True,'citations':[{'chunk_id':self.chunk.id,'quote':'Photosynthesis converts light energy into chemical energy.'}]}
        raw=json.dumps(output);parts=[raw[:35],raw[35:]]
        response=MagicMock();response.is_error=False;response.status_code=200
        response.iter_lines.return_value=['data: '+json.dumps({'candidates':[{'content':{'parts':[{'text':p}]}}]}) for p in parts]
        drafts=[];token=stream_callback.set(drafts.append)
        try:
            with patch('study.ai.httpx.stream') as stream:
                stream.return_value.__enter__.return_value=response
                result=generate(self.p,'tutor',TutorOutput,'Answer',{},[self.chunk.id])
        finally:stream_callback.reset(token)
        self.assertEqual(result.answer,output['answer']);self.assertEqual(drafts[-1],output['answer'])
        usage=AIUsage.objects.get();self.assertTrue(usage.success)
        self.assertEqual(usage.spans[-2]['stage'],'validation');self.assertNotIn('fixture-key',json.dumps(usage.spans))
    @override_settings(AI_PROVIDER='gemini')
    @patch.dict('os.environ',{'GEMINI_API_KEY':'fixture-key'})
    def test_invalid_stream_cannot_become_saved_answer(self):
        response=MagicMock();response.is_error=False;response.status_code=200
        response.iter_lines.return_value=['data: '+json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps({'answer':'Invented','supported':True,'citations':[]})}]}}]})]
        token=stream_callback.set(lambda text:None)
        try:
            with patch('study.ai.httpx.stream') as stream:
                stream.return_value.__enter__.return_value=response
                with self.assertRaises(AIError):tutor(self.user,self.p,'photosynthesis','invalid')
        finally:stream_callback.reset(token)
        self.assertFalse(Message.objects.exists());self.assertFalse(AIUsage.objects.get().success)
    def test_layout_tables_have_page_evidence(self):
        import tempfile,os
        file=BytesIO();c=Canvas(file);c.drawString(40,780,'Energy comparison table for studying photosynthesis.')
        for y in [700,670,640]:c.line(40,y,340,y)
        for x in [40,190,340]:c.line(x,640,x,700)
        c.drawString(50,680,'Process');c.drawString(200,680,'Location');c.drawString(50,650,'Calvin cycle');c.drawString(200,650,'Stroma');c.save()
        with tempfile.NamedTemporaryFile(suffix='.pdf',delete=False) as f:f.write(file.getvalue());name=f.name
        try:chunks,structure=extract_document(name)
        finally:os.unlink(name)
        self.assertEqual(structure['table_count'],1)
        self.assertTrue(any('Calvin cycle | Stroma' in text for _,_,text in chunks))
        self.assertTrue(all(page==1 for page,_,_ in chunks))
    def test_expired_jobs_have_retry_budget(self):
        Job.objects.create(material=self.m,owner=self.user,status='processing',attempts=3,available=timezone.now())
        Job.objects.update(updated=timezone.now()-timedelta(minutes=12))
        self.assertIsNone(claim_job());self.m.refresh_from_db();self.assertEqual(self.m.status,'failed')
    def test_analytics_breakdown_respects_filters(self):
        q=self.question();Assessment.objects.create(question=q,answer='0',score=1,feedback='Correct',before=.5,after=.66)
        rows=self.client.get(f'/api/projects/{self.p.id}/analytics/').data['breakdown']
        self.assertEqual(rows[0]['attempts'],1);self.assertEqual(rows[0]['score'],1)
        self.assertEqual(self.client.get(f'/api/projects/{self.p2.id}/analytics/').data['breakdown'],[])
        self.assertEqual(self.client.get(f'/api/projects/{self.p.id}/analytics/?from=2099-01-01').data['breakdown'],[])

    def test_pdf_retry_resumes_after_extraction(self):
        job=Job.objects.create(material=self.m,owner=self.user,available=timezone.now())
        claimed=claim_job()
        with patch('study.jobs.generate',side_effect=AIError('Quota exhausted')):process_job(claimed)
        self.m.refresh_from_db();self.assertTrue(self.m.structure)
        Job.objects.filter(id=job.id).update(available=timezone.now())
        claimed=claim_job()
        from .ai import ConceptsOutput
        chunk=self.m.chunks.first()
        output=ConceptsOutput(concepts=[{'name':'Light conversion','description':'Photosynthesis converts light to stored energy.','chunk_id':chunk.id}])
        with patch('study.jobs.extract_document',side_effect=AssertionError('Extraction repeated')),patch('study.jobs.generate',return_value=output):process_job(claimed)
        job.refresh_from_db();self.assertEqual(job.status,'ready');self.assertEqual(len(job.history),2)
    def test_insight_expired_lease_stops_after_budget(self):
        job=enqueue_insights(self.p,'expired')
        InsightJob.objects.filter(id=job.id).update(status='processing',attempts=3,updated=timezone.now()-timedelta(minutes=6))
        self.assertFalse(run_insight_job());job.refresh_from_db();self.assertEqual(job.status,'failed')
        self.client.post(f'/api/projects/{self.p.id}/insights/')
        self.assertTrue(InsightJob.objects.filter(project=self.p,status='queued').exists())

@override_settings(SECURE_SSL_REDIRECT=False)
class StreamingTransportTests(TransactionTestCase):
    setUp=fixtures.LearningTests.setUp
    def test_sse_unsupported_and_replay(self):
        path=f'/api/projects/{self.p.id}/tutor-stream/'
        for _ in range(2):
            response=self.client.post(path,{'question':'football scores','key':'same'})
            self.assertEqual(response.status_code,200)
            body=b''.join(response.streaming_content).decode()
            self.assertIn('event: complete',body);self.assertIn('enough evidence',body)
        self.assertEqual(Message.objects.count(),1)
        self.assertEqual(self.client.post(f'/api/projects/{self.foreign.id}/tutor-stream/',{'question':'secret','key':'x'}).status_code,404)
