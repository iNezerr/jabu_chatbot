from django.shortcuts import render
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import ChatMessageSerializer, ChatResponseSerializer, FeedbackSerializer
from .services import ChatService  # Use the simplified service
from .models import ChatLog, Feedback
from users.models import StudentProfile

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_message(request):
    """
    Chat endpoint for students to interact with the AI assistant
    
    POST Data:
        - message: Student's message or question (required)
        - student_id: Student's ID (required) - ID of the authenticated student
        - conversation_id: Conversation ID for continuing conversations (optional)
    """
    # Get student_id from the authenticated user if not provided
    data = request.data.copy()
    if not data.get('student_id'):
        try:
            student_profile = StudentProfile.objects.get(user=request.user)
            data['student_id'] = student_profile.student_id
        except StudentProfile.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Student profile not found for authenticated user'
            }, status=400)
    
    serializer = ChatMessageSerializer(data=data)
    
    if not serializer.is_valid():
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=400)
    
    # Extract data from request
    message = serializer.validated_data['message']
    student_id = serializer.validated_data['student_id']  # Now required
    conversation_id = serializer.validated_data.get('conversation_id')
    
    # Create chat service
    chat_service = ChatService()
    
    # Call the service to generate a response - now fully synchronous
    try:
        response_data = chat_service.generate_response(
            message, student_id, conversation_id
        )
        
        # Return response
        return Response({
            'status': 'success',
            'data': response_data
        }, status=200)
    except Exception as e:
        import traceback
        import logging
        
        logger = logging.getLogger(__name__)
        logger.error(f"Error in chat_message view: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Determine if this is a known error with a user-friendly message
        error_message = str(e)
        if "connection" in error_message.lower() or "timeout" in error_message.lower():
            user_message = "Unable to connect to the AI service. Please try again later."
        elif "api key" in error_message.lower() or "authentication" in error_message.lower():
            user_message = "Authentication error with the AI service. Please contact support."
        else:
            user_message = "An unexpected error occurred. Please try again later."
            
        return Response({
            'status': 'error',
            'message': user_message,
            'technical_details': error_message if settings.DEBUG else None
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_history(request):
    """
    Retrieve chat history for a specific conversation
    
    GET Parameters:
        - conversation_id: ID of the conversation to retrieve
    """
    conversation_id = request.GET.get('conversation_id')
    
    if not conversation_id:
        return Response({
            'status': 'error',
            'message': 'conversation_id is required'
        }, status=400)
    
    # Get chat logs for this conversation
    chat_logs = ChatLog.objects.filter(conversation_id=conversation_id).order_by('timestamp')
    
    # Format the chat history
    history = []
    for log in chat_logs:
        history.append({
            'user_message': log.user_message,
            'ai_response': log.ai_response,
            'timestamp': log.timestamp.isoformat()
        })
    
    return Response({
        'status': 'success',
        'data': {
            'conversation_id': conversation_id,
            'history': history
        }
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
