from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.
class KnowledgeBase(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    tags = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['last_updated']),
        ]
        verbose_name_plural = "Knowledge Base"
    
    def __str__(self):
        return self.title
