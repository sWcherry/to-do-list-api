from django.urls import path
from . import web_views

urlpatterns = [
    path('', web_views.home_view, name='home'),
    path('realtime-demo/', web_views.realtime_demo_view, name='realtime-demo'),
    path('admin-dashboard/', web_views.admin_dashboard_view, name='admin-dashboard'),
]