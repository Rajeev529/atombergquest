from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = [
        ('EMPLOYEE', 'Employee'),
        ('MANAGER', 'Manager'),
        ('ADMIN', 'Admin/HR'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='EMPLOYEE')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    theme_preference = models.CharField(max_length=50, default='ocean')
    unlocked_themes = models.JSONField(default=list)
    performance_score = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.username} ({self.role})"

    def calculate_performance_score(self):
        """Calculate performance score for theme unlocking"""
        if self.role == 'EMPLOYEE':
            goals = Goal.objects.filter(owner=self, status='APPROVED')
            if not goals.exists():
                return 0.0
            total_progress = 0
            goal_count = 0
            for goal in goals:
                achievements = QuarterlyAchievement.objects.filter(goal=goal)
                if achievements.exists():
                    latest = achievements.order_by('-quarter__end_date').first()
                    if latest.actual_value and goal.target_value:
                        if goal.uom_type in ['NUMERIC', 'PERCENTAGE'] and goal.uom_direction == 'MIN':
                            progress = (latest.actual_value / goal.target_value) * 100
                        elif goal.uom_type in ['NUMERIC', 'PERCENTAGE'] and goal.uom_direction == 'MAX':
                            progress = (goal.target_value / latest.actual_value) * 100 if latest.actual_value > 0 else 0
                        else:
                            progress = 50  # Default for other types
                        total_progress += min(progress, 100)
                        goal_count += 1
            return total_progress / goal_count if goal_count > 0 else 0.0
        
        elif self.role == 'MANAGER':
            subordinates = self.subordinates.all()
            if not subordinates.exists():
                return 0.0
            total = sum(sub.performance_score for sub in subordinates)
            return total / subordinates.count()
        
        return 0.0

    def update_unlocked_themes(self):
        """Update unlocked themes based on performance"""
        self.performance_score = self.calculate_performance_score()
        current_unlocked = set(self.unlocked_themes or [])
        # Always add free themes
        for theme_key, theme_data in settings.AVAILABLE_THEMES.items():
            if theme_data['free']:
                current_unlocked.add(theme_key)
            elif not theme_data['free'] and self.performance_score >= theme_data.get('required_performance', 100):
                current_unlocked.add(theme_key)
        self.unlocked_themes = list(current_unlocked)
        self.save(update_fields=['performance_score', 'unlocked_themes'])

class QuarterPeriod(models.Model):
    name = models.CharField(max_length=20, choices=settings.QUARTER_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    year = models.IntegerField(default=2025)

    def __str__(self):
        return f"{self.name} {self.year}"

    def is_open(self):
        if settings.DEMO_MODE:
            return True
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    class Meta:
        ordering = ['-year', 'start_date']

class Goal(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    thrust_area = models.CharField(max_length=50, choices=settings.THRUST_AREAS)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    uom_type = models.CharField(max_length=20, choices=settings.UOM_TYPES)
    uom_direction = models.CharField(max_length=10, choices=settings.UOM_DIRECTION, default='MIN')
    target_value = models.FloatField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    weightage = models.FloatField(validators=[MinValueValidator(10), MaxValueValidator(100)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_shared = models.BooleanField(default=False)
    shared_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_copies')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_goals')
    approved_at = models.DateTimeField(null=True, blank=True)
    locked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.owner.username}"

    def get_progress(self):
        """Calculate progress based on latest achievement"""
        latest_achievement = self.achievements.order_by('-quarter__start_date').first()
        if not latest_achievement or not latest_achievement.actual_value:
            return 0.0
        
        if self.uom_type in ['NUMERIC', 'PERCENTAGE']:
            if self.uom_direction == 'MIN':
                return (latest_achievement.actual_value / self.target_value) * 100 if self.target_value else 0
            else:
                return (self.target_value / latest_achievement.actual_value) * 100 if latest_achievement.actual_value > 0 else 0
        elif self.uom_type == 'TIMELINE':
            if latest_achievement.actual_date and self.target_date:
                return 100 if latest_achievement.actual_date <= self.target_date else 0
        elif self.uom_type == 'ZERO':
            return 100 if latest_achievement.actual_value == 0 else 0
        return 0

    def calculate_score(self):
        """Compute progress score for tracking"""
        progress = self.get_progress()
        return progress * (self.weightage / 100)

class QuarterlyAchievement(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='achievements')
    quarter = models.ForeignKey(QuarterPeriod, on_delete=models.CASCADE)
    actual_value = models.FloatField(null=True, blank=True)
    actual_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=settings.GOAL_STATUS, default='NOT_STARTED')
    comment = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['goal', 'quarter']

class ManagerCheckIn(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checkins')
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_checkins')
    quarter = models.ForeignKey(QuarterPeriod, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class SharedGoalDefinition(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thrust_area = models.CharField(max_length=50, choices=settings.THRUST_AREAS)
    target_value = models.FloatField()
    uom_type = models.CharField(max_length=20, choices=settings.UOM_TYPES)
    uom_direction = models.CharField(max_length=10, choices=settings.UOM_DIRECTION, default='MIN')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    primary_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='primary_shared_goals')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class SharedGoalAssignment(models.Model):
    shared_goal = models.ForeignKey(SharedGoalDefinition, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_shared_goals')
    weightage = models.FloatField(validators=[MinValueValidator(10), MaxValueValidator(100)])
    goal = models.OneToOneField(Goal, on_delete=models.CASCADE, null=True, blank=True)

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=200)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, null=True)
    changes = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"