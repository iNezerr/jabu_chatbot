from rest_framework import serializers
from .models import ChatLog, Feedback
from users.models import StudentProfile

class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
    student_id = serializers.CharField(required=True)
    conversation_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)

class ChatResponseSerializer(serializers.Serializer):
    response = serializers.CharField()
    conversation_id = serializers.CharField()
    sources = serializers.ListField(child=serializers.DictField(), required=False)
    
class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['chat_log', 'rating', 'comment']
