from django.contrib import admin
from .models import User, QuarterPeriod, Goal, QuarterlyAchievement, ManagerCheckIn, SharedGoalDefinition, SharedGoalAssignment, AuditLog

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'manager', 'performance_score']
    list_filter = ['role']

@admin.register(QuarterPeriod)
class QuarterPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'start_date', 'end_date', 'is_active']

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'status', 'weightage', 'locked']
    list_filter = ['status', 'thrust_area']

@admin.register(QuarterlyAchievement)
class QuarterlyAchievementAdmin(admin.ModelAdmin):
    list_display = ['goal', 'quarter', 'actual_value', 'status']

@admin.register(ManagerCheckIn)
class ManagerCheckInAdmin(admin.ModelAdmin):
    list_display = ['employee', 'manager', 'quarter']

@admin.register(SharedGoalDefinition)
class SharedGoalDefinitionAdmin(admin.ModelAdmin):
    list_display = ['title', 'primary_owner', 'created_by']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp']