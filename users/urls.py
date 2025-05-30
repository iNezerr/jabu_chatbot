from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'profiles', views.StudentProfileViewSet)

# The API URLs are determined automatically by the router
urlpatterns = [
    # Include the router generated URLs
    path('', include(router.urls)),
    # Custom profile endpoints for the currently authenticated user
    path('my-profile/', views.get_my_profile, name='my-profile'),
    path('my-profile/update/', views.update_my_profile, name='update-my-profile'),
]
