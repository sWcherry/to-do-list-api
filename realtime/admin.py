from django.contrib import admin
from .models import OnlineUser, UserActivity, RealtimeNotification

@admin.register(OnlineUser)
class OnlineUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'connected_at', 'last_activity', 'page_url']
    list_filter = ['connected_at', 'last_activity']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['connected_at']
    ordering = ['-last_activity']

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'description', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at', 'ip_address', 'user_agent']
    ordering = ['-created_at']

@admin.register(RealtimeNotification)
class RealtimeNotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'sender__username', 'title', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
