"""Durable, deterministic learning insights. No provider requests."""
import uuid
from datetime import timedelta
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import InsightJob, Project, Assessment, RetrievalCache

def enqueue_insights(project, revision):
    return InsightJob.objects.get_or_create(project=project,revision=revision,defaults={'available':timezone.now()})[0]

def run_insight_job():
    now = timezone.now()
    RetrievalCache.objects.filter(expires__lt=now).delete()
    stale = InsightJob.objects.filter(status='processing',updated__lt=now-timedelta(minutes=5))
    stale.filter(attempts__gte=3).update(status='failed',lease=None,error='Worker lease expired after 3 attempts.',updated=now)
    stale.filter(attempts__lt=3).update(status='queued',lease=None,available=now)
    for pk in InsightJob.objects.filter(status='queued',available__lte=now).values_list('id',flat=True)[:20]:
        lease = uuid.uuid4()
        if not InsightJob.objects.filter(id=pk,status='queued').update(status='processing',lease=lease,attempts=F('attempts')+1,updated=now): continue
        job = InsightJob.objects.select_related('project').get(id=pk)
        try:
            rows = list(Assessment.objects.filter(question__project=job.project).select_related('question__concept').order_by('-created')[:40])
            recent,previous = rows[:5],rows[5:10]
            average = lambda values: round(sum(a.score for a in values)/len(values),4) if values else None
            current,baseline = average(recent),average(previous)
            gaps = {}
            for a in rows:
                for missing in a.missing: gaps[missing] = gaps.get(missing,0)+1
            result = {'generated_at':now.isoformat(),'evidence_count':len(rows),'recent_score':current,'previous_score':baseline,
                'score_change':round(current-baseline,4) if current is not None and baseline is not None else None,
                'recurring_gaps':[{'name':k,'count':v} for k,v in sorted(gaps.items(),key=lambda x:-x[1])[:5]],
                'assessment_ids':[a.id for a in rows], 'method':'Last 5 assessments compared with the previous 5; up to 40 attempts for recurring gaps.'}
            with transaction.atomic():
                locked = InsightJob.objects.select_for_update().get(id=pk)
                if locked.lease != lease: return True
                p = Project.objects.select_for_update().get(id=job.project_id)
                p.context = {**p.context,'insights':result}
                p.save(update_fields=['context'])
                locked.status,locked.lease,locked.error,locked.result = 'ready',None,'',result
                locked.save()
        except Exception:
            InsightJob.objects.filter(id=pk,lease=lease).update(status='queued' if job.attempts<3 else 'failed',lease=None,error='Insight calculation failed. Retry available.',available=now+timedelta(seconds=20*2**job.attempts),updated=timezone.now())
        return True
    return False
