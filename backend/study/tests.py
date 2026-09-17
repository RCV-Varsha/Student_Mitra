import tempfile
from io import BytesIO
from unittest.mock import patch
from datetime import timedelta
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from pydantic import ValidationError
from reportlab.pdfgen.canvas import Canvas
from .models import *
from .ai import *
from .learning import *
from .jobs import *

def pdf_bytes(text='Photosynthesis converts light energy into chemical energy. Plants use carbon dioxide and water to make glucose and release oxygen.'):
    f=BytesIO(); c=Canvas(f); c.drawString(40,750,text); c.save(); return f.getvalue()

@override_settings(SECURE_SSL_REDIRECT=False,MEDIA_ROOT=tempfile.mkdtemp())
class LearningTests(TestCase):
    def setUp(self):
        U=get_user_model(); self.user=U.objects.create_user('learner',password='Safe-Password-123');self.other=U.objects.create_user('other',password='Safe-Password-123')
        self.s=Space.objects.create(owner=self.user,name='Science',description='Science learning')
        self.p=Project.objects.create(space=self.s,name='Biology',description='Plants',goal='Understand photosynthesis')
        self.p2=Project.objects.create(space=self.s,name='Other project',description='Isolated',goal='Different')
        self.foreign=Project.objects.create(space=Space.objects.create(owner=self.other,name='Private',description='Private'),name='Secret',description='Private',goal='Private')
        self.m=Material.objects.create(project=self.p,name='notes.pdf',file=SimpleUploadedFile('notes.pdf',pdf_bytes()),digest='abc',status='ready')
        self.chunk=Chunk.objects.create(material=self.m,page=1,ordinal=0,text='Photosynthesis converts light energy into chemical energy. Plants use carbon dioxide and water to make glucose and release oxygen.',embedding=vector('photosynthesis plants light energy glucose'))
        self.c=Concept.objects.create(project=self.p,name='Photosynthesis',description='Conversion of light to chemical energy',source=self.chunk)
        self.client=APIClient();self.client.force_authenticate(self.user)
    def question(self,kind='mcq'):
        return Question.objects.create(project=self.p,concept=self.c,key='q1',kind=kind,difficulty='foundation',prompt='What is converted by photosynthesis?',options=['Light','Sound','Heat','Wind'] if kind=='mcq' else [],correct=0 if kind=='mcq' else None,rubric=['Accuracy','Key concepts'],explanation='Plants convert light energy into chemical energy.',citations=[])
    def test_auth_required_and_admin_role(self):
        self.client.force_authenticate(None)
        self.assertIn(self.client.get('/api/projects/').status_code,[401,403])
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get('/api/admin/').status_code,403)
        self.user.is_staff=True;self.user.save()
        self.assertEqual(self.client.get('/api/admin/').status_code,200)
    def test_registration_cannot_grant_admin(self):
        self.client.force_authenticate(None)
        r=self.client.post('/api/auth/register/',{'username':'new','password':'Strong-long-7788','is_staff':True})
        self.assertEqual(r.status_code,200);self.assertFalse(get_user_model().objects.get(username='new').is_staff)
    def test_login_csrf_required(self):
        c=APIClient(enforce_csrf_checks=True)
        r=c.post('/api/auth/login/',{'username':'learner','password':'Safe-Password-123'})
        self.assertEqual(r.status_code,403)
    def test_foreign_project_endpoints_deny(self):
        for tail in ['', 'materials/','messages/','questions/','growth/','analytics/']:
            self.assertEqual(self.client.get(f'/api/projects/{self.foreign.id}/{tail}').status_code,404)
        self.assertEqual(self.client.post(f'/api/projects/{self.foreign.id}/events/',{'kind':'project_viewed','key':'x'}).status_code,404)
    def test_foreign_files_and_jobs_deny(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f'/api/materials/{self.m.id}/file/').status_code,404)
        self.assertEqual(self.client.post(f'/api/materials/{self.m.id}/retry/').status_code,404)
    def test_project_cannot_move_to_foreign_space(self):
        r=self.client.patch(f'/api/projects/{self.p.id}/',{'space':self.foreign.space_id})
        self.assertEqual(r.status_code,400)
    def test_retrieval_isolation_and_unsupported(self):
        self.assertEqual(retrieve(self.p2,'photosynthesis'),[])
        self.assertEqual(retrieve(self.p,'quantum cryptocurrency price'),[])
        self.assertEqual(retrieve(self.p,'photosynthesis light')[0].id,self.chunk.id)
        m=tutor(self.user,self.p,'Who won the football world cup?','unsupported')
        self.assertIn('enough evidence',m.answer);self.assertEqual(m.citations,[])
    def test_controlled_tools_reject_foreign_and_unknown(self):
        from django.http import Http404
        with self.assertRaises(Http404):execute_tool(self.other,{'name':'search_materials','project_id':self.p.id,'query':'light'})
        with self.assertRaises(ValidationError):ToolRequest.model_validate({'name':'execute_sql','project_id':self.p.id,'query':'SELECT *'})
    def test_citation_page_and_exact_quote(self):
        r=validate_citations([Citation(chunk_id=self.chunk.id,quote='Photosynthesis converts light energy')],[self.chunk])
        self.assertEqual(r[0]['page'],1);self.assertIn('#page=1',r[0]['url'])
        with self.assertRaises(AIError):validate_citations([Citation(chunk_id=self.chunk.id,quote='fabricated quote here')],[self.chunk])
        with self.assertRaises(AIError):validate_citations([Citation(chunk_id=999,quote='Photosynthesis converts light energy')],[self.chunk])
    @patch('study.learning.generate')
    def test_grounded_tutor_context_and_idempotency(self,mock):
        mock.return_value=TutorOutput(answer='Plants convert light into chemical energy.',supported=True,citations=[Citation(chunk_id=self.chunk.id,quote='Photosynthesis converts light energy into chemical energy.')])
        a=tutor(self.user,self.p,'Explain photosynthesis','same');b=tutor(self.user,self.p,'Explain photosynthesis','same')
        self.assertEqual(a.id,b.id);self.assertEqual(mock.call_count,1);self.assertEqual(Message.objects.count(),1)
        self.assertIn('context',mock.call_args.args[4]);self.assertEqual(a.citations[0]['material_id'],self.m.id)
    def test_invalid_structured_grade(self):
        with self.assertRaises(ValidationError):GradeOutput.model_validate({'criteria':[{'criterion':'a','score':2,'feedback':'wrong'}],'feedback':'No','missing':[]})
    def test_mcq_mastery_and_idempotency(self):
        q=self.question();a=grade(self.p,q,'0');b=grade(self.p,q,'1');self.c.refresh_from_db()
        self.assertEqual(a.id,b.id);self.assertGreater(self.c.mastery,.5);self.assertEqual(self.c.evidence_count,1)
        self.assertEqual(Event.objects.filter(kind='assessment_completed').count(),1)
        self.assertTrue(self.p.recommendations.exists())
    @patch('study.learning.generate')
    def test_open_grading_validated_rubric(self,mock):
        q=self.question('open')
        mock.return_value=GradeOutput(criteria=[Criterion(criterion='Wrong rubric',score=.5,feedback='Missing concepts'),Criterion(criterion='Key concepts',score=.5,feedback='Missing energy')],feedback='You need to explain the conversion.',missing=['energy'])
        with self.assertRaises(AIError):grade(self.p,q,'Plants use light.')
        self.assertEqual(Assessment.objects.count(),0)
        mock.return_value.criteria[0].criterion='Accuracy'
        a=grade(self.p,q,'Plants use light.');self.assertEqual(a.score,.5);self.assertEqual(a.missing,['energy'])
    def test_question_secret_not_exposed_and_cross_project_answer(self):
        q=self.question();data=self.client.get(f'/api/projects/{self.p.id}/questions/').json()[0]
        self.assertNotIn('correct',data);self.assertNotIn('rubric',data);self.assertNotIn('explanation',data)
        self.assertEqual(self.client.post(f'/api/projects/{self.p2.id}/questions/{q.id}/answer/',{'answer':'0'}).status_code,404)
    def test_adaptive_selection_uses_history_mistakes(self):
        c2=Concept.objects.create(project=self.p,name='Chlorophyll',description='Light capture',source=self.chunk,mastery=.5)
        for i in range(4):Question.objects.create(project=self.p,concept=self.c,key=f'h{i}',kind='mcq',difficulty='foundation',prompt='Past question',explanation='x')
        selected,difficulty,why=select_concept(self.p)
        self.assertEqual(selected.id,c2.id);self.assertIn('recent_performance',why)
        c2.mastery=.9;c2.evidence_count=5;c2.save();self.c.mistakes=4;self.c.save()
        self.assertEqual(select_concept(self.p)[0].id,self.c.id)
    def test_repeated_mistake_context_recommendation(self):
        self.c.mistakes=3;self.c.evidence_count=3;self.c.mastery=.3;self.c.save();refresh_context(self.p)
        self.assertEqual(self.p.context['repeated_mistakes'][0]['count'],3)
        r=self.p.recommendations.latest('id');self.assertIn('Photosynthesis',r.text);self.assertEqual(r.action,'Quiz')
    def test_events_idempotent_and_type_allowlist(self):
        payload={'kind':'project_viewed','key':'event-one'}
        a=self.client.post(f'/api/projects/{self.p.id}/events/',payload);b=self.client.post(f'/api/projects/{self.p.id}/events/',payload)
        self.assertEqual(a.json()['id'],b.json()['id'])
        self.assertEqual(self.client.post(f'/api/projects/{self.p.id}/events/',{'kind':'mastery_updated','key':'bad'}).status_code,400)
    def test_upload_duplicate_and_invalid(self):
        for i in range(2):
            r=self.client.post(f'/api/projects/{self.p.id}/materials/',{'file':SimpleUploadedFile('study.pdf',pdf_bytes())},format='multipart')
            self.assertEqual(r.status_code,201)
        # ReportLab stamps vary; use identical bytes for guaranteed dedup check.
        body=pdf_bytes();ids=[]
        for i in range(2):ids.append(self.client.post(f'/api/projects/{self.p.id}/materials/',{'file':SimpleUploadedFile('study.pdf',body)},format='multipart').json()['id'])
        self.assertEqual(ids[0],ids[1])
        self.assertEqual(self.client.post(f'/api/projects/{self.p.id}/materials/',{'file':SimpleUploadedFile('fake.pdf',b'not pdf')},format='multipart').status_code,400)
    @patch('study.jobs.generate')
    def test_job_success_claim_dedup(self,mock):
        job=Job.objects.create(material=self.m,owner=self.user,available=timezone.now())
        claimed=claim_job();self.assertIsNotNone(claimed);self.assertIsNone(claim_job())
        mock.side_effect=lambda p,f,s,t,payload,refs:ConceptsOutput(concepts=[ConceptOutput(name='Light energy',description='Converts light into energy',chunk_id=refs[0])])
        process_job(claimed);job.refresh_from_db();self.m.refresh_from_db()
        self.assertEqual(job.status,'ready');self.assertEqual(self.m.pages,1)
    @patch('study.jobs.generate',side_effect=AIError('Provider unavailable'))
    def test_job_retry_then_failed_then_manual_retry(self,mock):
        job=Job.objects.create(material=self.m,owner=self.user,available=timezone.now())
        for i in range(3):
            Job.objects.filter(id=job.id).update(available=timezone.now());process_job(claim_job())
        job.refresh_from_db();self.assertEqual(job.status,'failed');self.assertEqual(job.attempts,3)
        retry_job(self.m);job.refresh_from_db();self.assertEqual(job.status,'queued');self.assertEqual(job.attempts,0)
    def test_scanned_pdf_failure(self):
        self.m.file.save('blank.pdf',SimpleUploadedFile('blank.pdf',pdf_bytes('')))
        j=Job.objects.create(material=self.m,owner=self.user,available=timezone.now());process_job(claim_job());j.refresh_from_db()
        self.assertEqual(j.status,'failed');self.assertIn('OCR',j.error)
    def test_stale_lease_and_ownership(self):
        j=Job.objects.create(material=self.m,owner=self.other,available=timezone.now(),status='processing',lease=__import__('uuid').uuid4())
        Job.objects.filter(id=j.id).update(updated=timezone.now()-timedelta(minutes=11))
        claimed=claim_job();self.assertIsNotNone(claimed);process_job(claimed);j.refresh_from_db()
        self.assertEqual(j.status,'failed');self.assertIn('ownership',j.error)
    @patch('study.ai.httpx.post')
    @override_settings(AI_PROVIDER='openai')
    def test_provider_invalid_json_logged(self,mock):
        import os
        mock.return_value.status_code=200;mock.return_value.json.return_value={'choices':[{'message':{'content':'not json'}}],'usage':{'prompt_tokens':12,'completion_tokens':3}}
        with patch.dict(os.environ,{'OPENAI_API_KEY':'mock-key'}):
            with self.assertRaises(AIError):generate(self.p,'test',TutorOutput,'test',{})
        u=AIUsage.objects.latest('id');self.assertFalse(u.success);self.assertEqual(u.input_tokens,12)

    @patch('study.learning.generate')
    def test_unsupported_after_conversation_does_not_match_substrings(self,mock):
        Message.objects.create(project=self.p,key='prior',question='Explain photosynthesis',answer='Light to energy',citations=[])
        m=tutor(self.user,self.p,'What is the current price of bitcoin?','unsupported-after-prior')
        self.assertEqual(m.citations,[]);self.assertIn('enough evidence',m.answer);mock.assert_not_called()

    def test_database_failure_is_safe_retryable(self):
        from django.db import OperationalError
        from study.exceptions import api_exception_handler
        r=api_exception_handler(OperationalError('private database address'),{})
        self.assertEqual(r.status_code,503);self.assertNotIn('private database address',str(r.data))
