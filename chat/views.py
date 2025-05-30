from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import ChatMessageSerializer, ChatResponseSerializer, FeedbackSerializer
from .services import ChatService
from .models import ChatLog, Feedback
from users.models import StudentProfile
import asyncio

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def chat_message(request):
    """
    Chat endpoint for students to interact with the AI assistant
    
    POST Data:
        - message: Student's message or question (required)
        - student_id: Student's ID (optional)
        - conversation_id: Conversation ID for continuing conversations (optional)
    """
    serializer = ChatMessageSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=400)
    
    # Extract data from request
    message = serializer.validated_data['message']
    student_id = serializer.validated_data.get('student_id')
    conversation_id = serializer.validated_data.get('conversation_id')
    
    # Create chat service
    chat_service = ChatService()
    
    # Generate response (using await since this is an async view)
    response_data = await chat_service.generate_response(
        message, student_id, conversation_id
    )
    
    # Return response
    return Response({
        'status': 'success',
        'data': response_data
    }, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback(request):
    """
    Submit feedback for a chat interaction
    
    POST Data:
        - chat_log: ID of the chat log to rate (required)
        - rating: Rating from 1-5 (required)
        - comment: Optional comment (optional)
    """
    serializer = FeedbackSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=400)
    
    # Save feedback
    feedback = serializer.save()
    
    return Response({
        'status': 'success',
        'message': 'Feedback submitted successfully',
        'data': {
            'id': feedback.id,
            'rating': feedback.rating
        }
    }, status=201)
