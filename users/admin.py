from django.contrib import admin
from .models import StudentProfile

# Register your models here.
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'program', 'year_of_study', 'gpa', 'student_id')
    search_fields = ('name', 'email', 'program', 'student_id')
    list_filter = ('program', 'year_of_study')
