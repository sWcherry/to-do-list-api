from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'assigned_to', 'status', 'created_at', 'deadline']
    list_filter = ['status', 'created_at', 'owner']
    search_fields = ['title', 'description', 'owner__email', 'assigned_to__email']
    ordering = ['-created_at']
