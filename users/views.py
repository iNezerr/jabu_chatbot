from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import StudentProfile
from .serializers import StudentProfileSerializer, StudentProfileCreateUpdateSerializer
from django.shortcuts import get_object_or_404

# Create your views here.
class StudentProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations on StudentProfile
    """
    queryset = StudentProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action in ['create', 'update', 'partial_update']:
            return StudentProfileCreateUpdateSerializer
        return StudentProfileSerializer
    
    def perform_create(self, serializer):
        """Create profile and link to user"""
        serializer.save(user=self.request.user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_my_profile(request):
  """
  Create a profile for the currently authenticated user
  """
  # Check if profile already exists
  if StudentProfile.objects.filter(user=request.user).exists():
    return Response({
      'status': 'error',
      'message': 'Profile already exists for this user'
    }, status=status.HTTP_400_BAD_REQUEST)
  
  # Create new profile
  serializer = StudentProfileCreateUpdateSerializer(data=request.data)
  if serializer.is_valid():
    serializer.save(user=request.user)
    return Response({
      'status': 'success',
      'message': 'Profile created successfully',
      'data': serializer.data
    }, status=status.HTTP_201_CREATED)
  
  return Response({
    'status': 'error',
    'errors': serializer.errors
  }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_my_profile(request):
    """
    Get the profile of the currently authenticated user
    """
    try:
        profile = StudentProfile.objects.get(user=request.user)
        serializer = StudentProfileSerializer(profile)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    except StudentProfile.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Profile not found for this user'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_my_profile(request):
    """
    Update the profile of the currently authenticated user
    """
    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Profile not found for this user'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = StudentProfileCreateUpdateSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'status': 'success',
            'message': 'Profile updated successfully',
            'data': serializer.data
        })
    return Response({
        'status': 'error',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)
