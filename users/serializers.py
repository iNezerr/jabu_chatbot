from rest_framework import serializers
from .models import StudentProfile

class StudentProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for StudentProfile model
    """
    class Meta:
        model = StudentProfile
        fields = ['id', 'user', 'name', 'email', 'program', 'year_of_study', 
                  'gpa', 'student_id', 'bio', 'date_joined', 'last_updated']
        read_only_fields = ['date_joined', 'last_updated']
        
class StudentProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating StudentProfile
    """
    class Meta:
        model = StudentProfile
        fields = ['name', 'email', 'program', 'year_of_study', 'gpa', 'student_id', 'bio']
