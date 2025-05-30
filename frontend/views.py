from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def index(request):
    """Homepage view"""
    return render(request, 'frontend/index.html')

def login_view(request):
    """Login page view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'frontend/login.html')

def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('index')

@login_required
def dashboard(request):
    """Main dashboard view (protected)"""
    return render(request, 'frontend/dashboard.html')

@login_required
def chat_view(request):
    """Chat interface view (protected)"""
    return render(request, 'frontend/chat.html')

@login_required
def profile_view(request):
    """User profile view (protected)"""
    return render(request, 'frontend/profile.html')

@login_required
def crawler_view(request):
    """Crawler management view (admin only)"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    return render(request, 'frontend/crawler.html')
