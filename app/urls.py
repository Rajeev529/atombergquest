
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/',views.custom_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-goal/', views.create_goal, name='create_goal'),
    path('approve-goals/', views.approve_goals, name='approve_goals'),
    path('quarterly-update/', views.quarterly_update, name='quarterly_update'),
    path('team-checkins/', views.team_checkins, name='team_checkins'),
    path('create-shared-goal/', views.create_shared_goal, name='create_shared_goal'),
    path('assign-shared-goal/<int:shared_goal_id>/', views.assign_shared_goal, name='assign_shared_goal'),
    path('report/', views.achievement_report, name='report'),
    path('completion-dashboard/', views.completion_dashboard, name='completion_dashboard'),
    path('change-theme/', views.change_theme, name='change_theme'),
    path('audit-log/', views.audit_log_view, name='audit_log'),
    path('analytics/', views.analytics_view, name='analytics'),
]