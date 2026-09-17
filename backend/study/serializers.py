from rest_framework import serializers
from .models import *

class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = ['id','name','description','created']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id','space','name','description','goal','context','is_demo','created','updated']
        read_only_fields = ['context','is_demo']
    def validate_space(self, value):
        if value.owner_id != self.context['request'].user.id: raise serializers.ValidationError('Space not found.')
        return value

class MaterialSerializer(serializers.ModelSerializer):
    attempts = serializers.IntegerField(source='job.attempts',read_only=True)
    class Meta:
        model = Material
        fields = ['id','project','name','status','pages','warning','created','attempts']

class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = ['id','name','description','mastery','evidence_count','mistakes','source','updated']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id','question','answer','citations','created']

class AssessmentSerializer(serializers.ModelSerializer):
    concept = serializers.CharField(source='question.concept.name')
    citations = serializers.JSONField(source='question.citations',read_only=True)
    class Meta:
        model = Assessment
        fields = ['id','question','concept','answer','score','feedback','criteria','missing','before','after','created','citations']

class QuestionSerializer(serializers.ModelSerializer):
    concept_name = serializers.CharField(source='concept.name')
    assessment = AssessmentSerializer(read_only=True)
    class Meta:
        model = Question
        fields = ['id','concept_name','kind','difficulty','prompt','options','selection','created','assessment']

class TutorInput(serializers.Serializer):
    question = serializers.CharField(max_length=2000)
    key = serializers.CharField(max_length=100)

class QuizInput(serializers.Serializer):
    kind = serializers.ChoiceField(choices=['mcq','open'])
    key = serializers.CharField(max_length=100)

class AnswerInput(serializers.Serializer):
    answer = serializers.CharField(max_length=5000,trim_whitespace=True)
