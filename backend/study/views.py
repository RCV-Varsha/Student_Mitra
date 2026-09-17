import hashlib
from datetime import timedelta
from pathlib import Path
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, connection
from django.db.models import Avg, Sum, Count
from django.db.models.functions import TruncDate
from django.http import FileResponse, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import *
from .serializers import *
from .learning import owned, tutor, create_question, grade, refresh_context, event
from .ai import AIError
from .jobs import retry_job

def user_data(u): return {'id':u.id,'username':u.username,'is_admin':u.is_staff}

@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def session(request):
    return Response({'user':user_data(request.user) if request.user.is_authenticated else None,'csrf':get_token(request)})

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_protect
def auth(request, action):
    username,password = request.data.get('username',''),request.data.get('password','')
    if not isinstance(username,str) or not isinstance(password,str) or len(username)>150 or len(password)>200:
        raise ValidationError('Invalid credentials.')
    if action == 'register':
        if not username.strip(): raise ValidationError('Username is required.')
        try: validate_password(password)
        except DjangoValidationError as e: raise ValidationError(e.messages)
        if get_user_model().objects.filter(username=username).exists(): raise ValidationError('Username already exists.')
        u = get_user_model().objects.create_user(username=username,password=password)
    elif action == 'login':
        u = authenticate(request,username=username,password=password)
        if not u: return Response({'detail':'Incorrect username or password.'},status=400)
    else: return Response(status=404)
    login(request,u)
    return Response({'user':user_data(u),'csrf':get_token(request)})

@api_view(['POST'])
def signout(request):
    logout(request)
    return Response({'ok':True})

@api_view(['GET','POST'])
def spaces(request):
    if request.method == 'GET': return Response(SpaceSerializer(Space.objects.filter(owner=request.user).order_by('id'),many=True).data)
    s = SpaceSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    s.save(owner=request.user)
    return Response(s.data,status=201)

@api_view(['GET','POST'])
def projects(request):
    if request.method == 'GET':
        return Response(ProjectSerializer(Project.objects.filter(space__owner=request.user).order_by('-updated'),many=True).data)
    s = ProjectSerializer(data=request.data,context={'request':request})
    s.is_valid(raise_exception=True)
    p = s.save()
    event(p,'project_created',f'created:{p.id}')
    refresh_context(p)
    return Response(ProjectSerializer(p).data,status=201)

@api_view(['GET','PATCH'])
def project_detail(request,pk):
    p = owned(request.user,pk)
    if request.method == 'PATCH':
        s = ProjectSerializer(p,data=request.data,partial=True,context={'request':request})
        s.is_valid(raise_exception=True)
        s.save()
        refresh_context(p)
    return Response(ProjectSerializer(p).data)

@api_view(['GET','POST'])
def materials(request,pk):
    p = owned(request.user,pk)
    if request.method == 'GET': return Response(MaterialSerializer(p.materials.select_related('job').order_by('-created'),many=True).data)
    f = request.FILES.get('file')
    if not f or not f.name.lower().endswith('.pdf'): raise ValidationError('Choose a PDF file.')
    if f.size>20*1024*1024: raise ValidationError('Maximum file size is 20 MB.')
    head = f.read(5)
    if head != b'%PDF-': raise ValidationError('The file is not a valid PDF.')
    f.seek(0)
    digest = hashlib.sha256()
    for block in f.chunks(): digest.update(block)
    f.seek(0)
    with transaction.atomic():
        # Serialize same-project uploads to avoid orphaned duplicate files.
        Project.objects.select_for_update().get(id=p.id)
        m = p.materials.filter(digest=digest.hexdigest()).first()
        if not m:
            m = Material.objects.create(project=p,name=Path(f.name).name[:200],file=f,digest=digest.hexdigest())
            Job.objects.create(material=m,owner=request.user,available=timezone.now())
            event(p,'material_uploaded',f'upload:{m.id}')
    return Response(MaterialSerializer(m).data,status=201)

@api_view(['GET'])
def material_file(request,pk):
    m = get_object_or_404(Material,id=pk,project__space__owner=request.user)
    r = FileResponse(m.file.open('rb'),content_type='application/pdf')
    r['Content-Disposition'] = 'inline; filename="material.pdf"'
    r['Content-Security-Policy'] = "sandbox"
    r['Cache-Control'] = 'private, no-store'
    return r

@api_view(['POST'])
def retry(request,pk):
    m = get_object_or_404(Material,id=pk,project__space__owner=request.user)
    try: retry_job(m)
    except ValueError as e: raise ValidationError(str(e))
    return Response(MaterialSerializer(m).data)

@api_view(['GET','POST'])
def messages(request,pk):
    p = owned(request.user,pk)
    if request.method == 'GET': return Response(MessageSerializer(p.messages.order_by('-created')[:50],many=True).data[::-1])
    s = TutorInput(data=request.data); s.is_valid(raise_exception=True)
    try: m = tutor(request.user,p,**s.validated_data)
    except AIError as e: return Response({'detail':str(e)},status=503)
    except ValueError as e: raise ValidationError(str(e))
    return Response(MessageSerializer(m).data)

@api_view(['GET','POST'])
def questions(request,pk):
    p = owned(request.user,pk)
    if request.method == 'GET': return Response(QuestionSerializer(p.questions.select_related('concept','assessment').order_by('-created')[:30],many=True).data)
    s = QuizInput(data=request.data); s.is_valid(raise_exception=True)
    try: q = create_question(p,**s.validated_data)
    except AIError as e: return Response({'detail':str(e)},status=503)
    except ValueError as e: raise ValidationError(str(e))
    return Response(QuestionSerializer(q).data)

@api_view(['POST'])
def answer(request,pk,qid):
    p = owned(request.user,pk)
    q = get_object_or_404(Question,id=qid,project=p)
    s = AnswerInput(data=request.data); s.is_valid(raise_exception=True)
    try: a = grade(p,q,s.validated_data['answer'])
    except AIError as e: return Response({'detail':str(e)},status=503)
    except ValueError as e: raise ValidationError(str(e))
    return Response({**AssessmentSerializer(a).data,'citations':q.citations,'rubric':q.rubric})

@api_view(['GET'])
def growth(request,pk):
    p = owned(request.user,pk)
    return Response({'concepts':ConceptSerializer(p.concepts.order_by('mastery'),many=True).data,'history':AssessmentSerializer(Assessment.objects.filter(question__project=p).select_related('question__concept').order_by('-created')[:100],many=True).data,'recommendations':list(p.recommendations.order_by('-created').values('id','text','action','concept_id','created')[:5]),'context':p.context})

@api_view(['POST'])
def activity(request,pk):
    p = owned(request.user,pk)
    kind,key = request.data.get('kind'),request.data.get('key')
    if kind not in ['project_viewed','material_viewed'] or not isinstance(key,str) or not 1<=len(key)<=100: raise ValidationError('Invalid activity event.')
    e = event(p,kind,'client:'+key)
    return Response({'id':e.id})

def analytics_data(projects, params):
    events = Event.objects.filter(project__in=projects)
    assessments = Assessment.objects.filter(question__project__in=projects)
    usage = AIUsage.objects.filter(project__in=projects)
    for field,lookup in [('from','created__date__gte'),('to','created__date__lte')]:
        val = params.get(field)
        if val:
            from datetime import date
            try: date.fromisoformat(val)
            except ValueError: raise ValidationError('Dates must be YYYY-MM-DD.')
            events,assessments,usage = events.filter(**{lookup:val}),assessments.filter(**{lookup:val}),usage.filter(**{lookup:val})
    if params.get('type'): events = events.filter(kind=params['type'])
    concepts = Concept.objects.filter(project__in=projects)
    return {'projects':projects.count(),'materials':Material.objects.filter(project__in=projects,status='ready').count(),'events':events.count(),'assessments':assessments.count(),'average_score':assessments.aggregate(v=Avg('score'))['v'],'mastery':concepts.filter(evidence_count__gt=0).aggregate(v=Avg('mastery'))['v'],'assessed_concepts':concepts.filter(evidence_count__gt=0).count(),'concepts':concepts.count(),'attention':ConceptSerializer(concepts.filter(evidence_count__gt=0,mastery__lt=.6).order_by('mastery')[:8],many=True).data,
      'activity':list(events.annotate(day=TruncDate('created')).values('day').annotate(count=Count('id')).order_by('day')),
      'performance':list(assessments.annotate(day=TruncDate('created')).values('day').annotate(score=Avg('score')).order_by('day')),
      'usage':{'calls':usage.count(),'failed':usage.filter(success=False).count(),**usage.aggregate(input_tokens=Sum('input_tokens'),output_tokens=Sum('output_tokens'),estimated_cost=Sum('estimated_cost'),latency_ms=Avg('latency_ms'))},
      'recent_events':list(events.order_by('-created').values('id','kind','project_id','project__name','project__space__owner__username','data','created')[:100]),
      'usage_log':list(usage.order_by('-created').values('id','feature','model','latency_ms','input_tokens','output_tokens','estimated_cost','success','error','sources','created')[:50])}

@api_view(['GET'])
def analytics(request,pk=None):
    ps = Project.objects.filter(space__owner=request.user)
    if pk: ps = ps.filter(id=owned(request.user,pk).id)
    return Response(analytics_data(ps,request.query_params))

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard(request):
    ps = Project.objects.all()
    for param,field in [('user','space__owner_id'),('space','space_id'),('project','id')]:
        if request.query_params.get(param):
            try: val = int(request.query_params[param])
            except ValueError: raise ValidationError('Filters require numeric IDs.')
            ps = ps.filter(**{field:val})
    heartbeat = Heartbeat.objects.order_by('-updated').first()
    data = analytics_data(ps,request.query_params)
    assessment_rows = Assessment.objects.filter(question__project__in=ps)
    job_rows = Job.objects.filter(material__project__in=ps)
    for param,lookup in [('from','gte'),('to','lte')]:
        value = request.query_params.get(param)
        if value:
            assessment_rows = assessment_rows.filter(**{f'created__date__{lookup}':value})
            job_rows = job_rows.filter(**{f'updated__date__{lookup}':value})
    data.update({'users':list(get_user_model().objects.values('id','username','is_staff','date_joined','last_login')),'spaces':list(Space.objects.values('id','name','owner_id')),'project_list':list(ps.values('id','name','space_id','space__owner_id')),'assessments_log':AssessmentSerializer(assessment_rows.select_related('question__concept').order_by('-created')[:100],many=True).data,'jobs':list(job_rows.values('id','status','attempts','error','updated','material__name','material__project_id','owner_id')),'evaluations':list(Evaluation.objects.order_by('-created').values()[:10]),'health':{'database':connection.vendor,'worker':'healthy' if heartbeat and heartbeat.updated>timezone.now()-timedelta(minutes=3) else 'offline or stale','worker_last_seen':heartbeat.updated if heartbeat else None,'ai_configured':bool(__import__('os').getenv('OPENAI_API_KEY') or __import__('os').getenv('GEMINI_API_KEY'))}})
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    with connection.cursor() as cursor: cursor.execute('SELECT 1')
    return Response({'status':'ok'})

def frontend(request):
    path = settings.BASE_DIR.parent/'frontend/dist/index.html'
    return HttpResponse(path.read_text(encoding='utf-8') if path.exists() else 'Build frontend with npm run build.',content_type='text/html')
