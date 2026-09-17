import uuid
from django.conf import settings
from django.db import models
from pgvector.django import VectorField

class Space(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    description = models.TextField(max_length=2000)
    created = models.DateTimeField(auto_now_add=True)

class Project(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=120)
    description = models.TextField(max_length=2000)
    goal = models.TextField(max_length=2000)
    context = models.JSONField(default=dict)
    is_demo = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

def private_path(instance, filename):
    return f'{instance.project.space.owner_id}/{instance.project_id}/{uuid.uuid4()}.pdf'

class Material(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='materials')
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to=private_path)
    digest = models.CharField(max_length=64)
    status = models.CharField(max_length=20, default='queued')
    pages = models.PositiveIntegerField(default=0)
    warning = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['project','digest'],name='unique_project_document')]

class Chunk(models.Model):
    material = models.ForeignKey(Material,on_delete=models.CASCADE,related_name='chunks')
    page = models.PositiveIntegerField()
    ordinal = models.PositiveIntegerField()
    text = models.TextField()
    embedding = VectorField(dimensions=256,null=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['material','page','ordinal'],name='unique_page_chunk')]

class Concept(models.Model):
    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name='concepts')
    name = models.CharField(max_length=150)
    description = models.TextField()
    source = models.ForeignKey(Chunk,on_delete=models.SET_NULL,null=True)
    mastery = models.FloatField(default=0.5)
    evidence_count = models.PositiveIntegerField(default=0)
    mistakes = models.PositiveIntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['project','name'],name='unique_project_concept')]

class Job(models.Model):
    material = models.OneToOneField(Material,on_delete=models.CASCADE,related_name='job')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    status = models.CharField(max_length=20,default='queued',db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    lease = models.UUIDField(null=True)
    available = models.DateTimeField()
    updated = models.DateTimeField(auto_now=True)

class Heartbeat(models.Model):
    name = models.CharField(max_length=120,unique=True)
    updated = models.DateTimeField(auto_now=True)

class Event(models.Model):
    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name='events')
    kind = models.CharField(max_length=60)
    key = models.CharField(max_length=160)
    data = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True,db_index=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['project','key'],name='unique_event_key')]

class Message(models.Model):
    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name='messages')
    key = models.CharField(max_length=100)
    question = models.TextField()
    answer = models.TextField()
    citations = models.JSONField(default=list)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['project','key'],name='unique_message_key')]

class Question(models.Model):
    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name='questions')
    concept = models.ForeignKey(Concept,on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    kind = models.CharField(max_length=20)
    difficulty = models.CharField(max_length=20)
    prompt = models.TextField()
    options = models.JSONField(default=list)
    correct = models.IntegerField(null=True)
    rubric = models.JSONField(default=list)
    explanation = models.TextField()
    citations = models.JSONField(default=list)
    selection = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['project','key'],name='unique_question_key')]

class Assessment(models.Model):
    question = models.OneToOneField(Question,on_delete=models.CASCADE,related_name='assessment')
    answer = models.TextField()
    score = models.FloatField()
    feedback = models.TextField()
    criteria = models.JSONField(default=list)
    missing = models.JSONField(default=list)
    before = models.FloatField()
    after = models.FloatField()
    created = models.DateTimeField(auto_now_add=True)

class Recommendation(models.Model):
    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name='recommendations')
    concept = models.ForeignKey(Concept,on_delete=models.SET_NULL,null=True)
    text = models.TextField()
    action = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)

class AIUsage(models.Model):
    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name='ai_usage')
    feature = models.CharField(max_length=40)
    model = models.CharField(max_length=120)
    latency_ms = models.PositiveIntegerField(default=0)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    estimated_cost = models.FloatField(default=0)
    success = models.BooleanField(default=False)
    error = models.CharField(max_length=300,blank=True)
    sources = models.JSONField(default=list)
    created = models.DateTimeField(auto_now_add=True)

class Evaluation(models.Model):
    mode = models.CharField(max_length=20)
    results = models.JSONField(default=list)
    passed = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
