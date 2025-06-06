"""
Authentication URLs for token-based authentication
"""
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('token/', obtain_auth_token, name='api-token'),
]
