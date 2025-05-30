from django.contrib import admin
from .models import ChatLog, Feedback

# Register your models here.
@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'short_message', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user_message', 'ai_response', 'student__name')
    date_hierarchy = 'timestamp'
    
    def short_message(self, obj):
        return obj.user_message[:50] + '...' if len(obj.user_message) > 50 else obj.user_message
    
    short_message.short_description = 'User Message'


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('chat_log', 'rating', 'submitted_at')
    list_filter = ('rating', 'submitted_at')
    search_fields = ('comment', 'chat_log__user_message')
