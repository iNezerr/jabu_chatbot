from django.contrib import admin
from .models import KnowledgeBase

# Register your models here.
@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'source_url', 'last_updated', 'is_verified')
    list_filter = ('is_verified', 'last_updated')
    search_fields = ('title', 'content', 'tags')
    date_hierarchy = 'last_updated'
