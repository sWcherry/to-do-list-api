from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from tasks.models import Task
from .models import OnlineUser

User = get_user_model()

def home_view(request):
    """Головна сторінка"""
    online_count = OnlineUser.get_online_count()
    
    context = {
        'online_count': online_count,
    }
    return render(request, 'realtime/home.html', context)

@login_required
def realtime_demo_view(request):
    """Демонстрація real-time функцій"""
    tasks = Task.objects.filter(
        owner=request.user
    ) | Task.objects.filter(
        assigned_to=request.user
    )

    context = {
        'tasks': tasks.distinct(),
        'user': request.user,
        'users': User.objects.all()
    }
    return render(request, 'realtime/demo.html', context)

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard_view(request):
    """Адміністративна панель для перегляду онлайн користувачів"""
    context = {
        'user': request.user,
    }
    return render(request, 'realtime/admin_dashboard.html', context)