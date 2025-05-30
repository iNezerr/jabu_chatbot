from django.urls import path
from . import views

urlpatterns = [
    path('refresh-knowledgebase/', views.refresh_knowledgebase, name='refresh-knowledgebase'),
    path('search/', views.search_kb, name='search-knowledge-base'),
]
