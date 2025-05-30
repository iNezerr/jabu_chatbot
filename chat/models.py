from django.db import models
from users.models import StudentProfile

# Create your models here.
class ChatLog(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="chats")
    user_message = models.TextField()
    ai_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    conversation_id = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Chat with {self.student.name} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class Feedback(models.Model):
    RATING_CHOICES = [
        (1, '1 - Not helpful at all'),
        (2, '2 - Slightly helpful'),
        (3, '3 - Moderately helpful'),
        (4, '4 - Very helpful'),
        (5, '5 - Extremely helpful'),
    ]
    
    chat_log = models.ForeignKey(ChatLog, on_delete=models.CASCADE, related_name="feedbacks")
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback for chat #{self.chat_log.id} - Rating: {self.rating}"
