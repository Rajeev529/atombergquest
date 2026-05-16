from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Q, Avg
from django.utils import timezone
from datetime import datetime
import csv
from .models import *
from .forms import GoalForm, GoalApprovalForm, QuarterlyAchievementForm, SharedGoalForm, BulkAssignForm

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in allowed_roles:
                messages.error(request, 'Access denied')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

import json
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone

@login_required
def dashboard(request):
    user = request.user
    user.update_unlocked_themes()
    context = {'user': user}
    
    if user.role == 'EMPLOYEE':
        goals = Goal.objects.filter(owner=user)
        pending_goals = goals.filter(status='PENDING')
        approved_goals = goals.filter(status='APPROVED')
        
        # Check goal setting window
        goal_setting_quarter = QuarterPeriod.objects.filter(name='GOAL_SETTING', is_active=True).first()
        can_create_goals = goal_setting_quarter.is_open() if goal_setting_quarter else False
        
        # Calculate overall progress
        total_score = sum(g.calculate_score() for g in approved_goals)
        
        # ----- Chart Data -----
        # 1. Goal progress per goal (bar chart)
        goal_labels = [g.title[:15] for g in approved_goals]
        goal_progress = [g.get_progress() for g in approved_goals]
        goal_weights = [g.weightage for g in approved_goals]
        
        # 2. Quarterly performance trend (last 4 quarters)
        quarters = QuarterPeriod.objects.exclude(name='GOAL_SETTING').order_by('start_date')[:4]
        quarter_labels = [f"{q.name} {q.year}" for q in quarters]
        quarterly_scores = []
        for q in quarters:
            achievements = QuarterlyAchievement.objects.filter(goal__owner=user, quarter=q)
            if achievements.exists():
                avg_progress = achievements.aggregate(Avg('actual_value'))['actual_value__avg'] or 0
            else:
                avg_progress = 0
            quarterly_scores.append(avg_progress)
        
        # 3. Thrust area distribution (pie chart)
        thrust_counts = goals.filter(status='APPROVED').values('thrust_area').annotate(count=Count('id'))
        thrust_labels = [item['thrust_area'] for item in thrust_counts]
        thrust_values = [item['count'] for item in thrust_counts]
        
        context.update({
            'total_goals': goals.count(),
            'pending_goals': pending_goals.count(),
            'approved_goals': approved_goals.count(),
            'can_create_goals': can_create_goals,
            'overall_progress': total_score,
            'goals': goals,
            # Charts JSON
            'goal_labels_json': json.dumps(goal_labels),
            'goal_progress_json': json.dumps(goal_progress),
            'goal_weights_json': json.dumps(goal_weights),
            'quarter_labels_json': json.dumps(quarter_labels),
            'quarterly_scores_json': json.dumps(quarterly_scores),
            'thrust_labels_json': json.dumps(thrust_labels),
            'thrust_values_json': json.dumps(thrust_values),
        })
        
    elif user.role == 'MANAGER':
        subordinates = user.subordinates.all()
        pending_approvals = Goal.objects.filter(owner__in=subordinates, status='PENDING')
        teams_goals = Goal.objects.filter(owner__in=subordinates, status='APPROVED')
        
        total_employees = subordinates.count()
        completed_checkins = ManagerCheckIn.objects.filter(manager=user, quarter__is_active=True).values('employee').distinct().count()
        checkin_rate = (completed_checkins / total_employees * 100) if total_employees > 0 else 0
        
        # Team performance data for chart
        team_performance = []
        for emp in subordinates:
            emp_score = emp.calculate_performance_score() if hasattr(emp, 'calculate_performance_score') else 0
            team_performance.append({'name': emp.username, 'score': emp_score})
        
        # Average team progress over time (quarterly)
        quarters = QuarterPeriod.objects.exclude(name='GOAL_SETTING').order_by('start_date')[:4]
        quarter_labels = [f"{q.name} {q.year}" for q in quarters]
        team_avg_progress = []
        for q in quarters:
            avg = QuarterlyAchievement.objects.filter(goal__owner__in=subordinates, quarter=q).aggregate(Avg('actual_value'))['actual_value__avg'] or 0
            team_avg_progress.append(avg)
        
        context.update({
            'subordinates': subordinates,
            'pending_approvals': pending_approvals.count(),
            'team_goals': teams_goals.count(),
            'team_size': total_employees,
            'checkin_completion': checkin_rate,
            'team_performance_json': json.dumps(team_performance),
            'quarter_labels_json': json.dumps(quarter_labels),
            'team_avg_progress_json': json.dumps(team_avg_progress),
        })
        
    elif user.role == 'ADMIN':
        total_users = User.objects.count()
        total_goals = Goal.objects.count()
        approved_goals = Goal.objects.filter(status='APPROVED').count()
        completion_rate = (approved_goals / total_goals * 100) if total_goals > 0 else 0
        
        # Department-wise goal distribution
        thrust_distribution = Goal.objects.values('thrust_area').annotate(count=Count('id')).order_by('-count')
        thrust_labels = [item['thrust_area'] for item in thrust_distribution]
        thrust_counts = [item['count'] for item in thrust_distribution]
        
        # Quarter-on-Quarter organization progress
        quarters = QuarterPeriod.objects.exclude(name='GOAL_SETTING').order_by('start_date')[:4]
        quarter_labels = [f"{q.name} {q.year}" for q in quarters]
        org_qoq_progress = []
        for q in quarters:
            avg = QuarterlyAchievement.objects.filter(quarter=q).aggregate(Avg('actual_value'))['actual_value__avg'] or 0
            org_qoq_progress.append(avg)
        
        # Top performing employees
        top_employees = User.objects.filter(role='EMPLOYEE').order_by('-performance_score')[:5]
        
        context.update({
            'total_users': total_users,
            'total_goals': total_goals,
            'completion_rate': completion_rate,
            'pending_approvals': Goal.objects.filter(status='PENDING').count(),
            'thrust_labels_json': json.dumps(thrust_labels),
            'thrust_counts_json': json.dumps(thrust_counts),
            'quarter_labels_json': json.dumps(quarter_labels),
            'org_qoq_progress_json': json.dumps(org_qoq_progress),
            'top_employees': top_employees,
        })
    
    return render(request, 'goals/dashboard.html', context)

@login_required
@role_required(['EMPLOYEE'])
def create_goal(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.owner = request.user
            goal.status = 'PENDING'
            
            # Check total weightage
            existing_goals = Goal.objects.filter(owner=request.user, status__in=['DRAFT', 'PENDING', 'APPROVED'])
            total_weight = sum(g.weightage for g in existing_goals) + goal.weightage
            
            if existing_goals.count() >= 8:
                messages.error(request, 'Maximum 8 goals allowed per employee')
            elif total_weight > 100:
                messages.error(request, f'Total weightage would exceed 100%. Current total: {total_weight - goal.weightage}%')
            else:
                goal.save()
                messages.success(request, 'Goal submitted for approval')
                return redirect('dashboard')
    else:
        form = GoalForm()
    
    return render(request, 'goals/create_goal.html', {'form': form})

@login_required
@role_required(['MANAGER'])
def approve_goals(request):
    subordinates = request.user.subordinates.all()
    pending_goals = Goal.objects.filter(owner__in=subordinates, status='PENDING')
    
    if request.method == 'POST':
        goal_id = request.POST.get('goal_id')
        action = request.POST.get('action')
        goal = get_object_or_404(Goal, id=goal_id)
        
        if action == 'approve':
            goal.status = 'APPROVED'
            goal.approved_by = request.user
            goal.approved_at = timezone.now()
            goal.locked = True
            goal.save()
            messages.success(request, f'Goal "{goal.title}" approved')
        elif action == 'reject':
            goal.status = 'REJECTED'
            goal.save()
            messages.warning(request, f'Goal "{goal.title}" rejected')
        elif action == 'edit':
            new_weightage = request.POST.get('weightage')
            new_target = request.POST.get('target_value')
            if new_weightage:
                goal.weightage = float(new_weightage)
            if new_target:
                goal.target_value = float(new_target)
            goal.status = 'APPROVED'
            goal.approved_by = request.user
            goal.approved_at = timezone.now()
            goal.locked = True
            goal.save()
            messages.success(request, f'Goal "{goal.title}" approved with modifications')
        
        return redirect('approve_goals')
    
    return render(request, 'goals/approve_goals.html', {'pending_goals': pending_goals})

@login_required
@role_required(['EMPLOYEE'])
def quarterly_update(request):
    user = request.user
    goals = Goal.objects.filter(owner=user, status='APPROVED')
    current_quarter = QuarterPeriod.objects.filter(is_active=True).first()
    
    if not current_quarter or current_quarter.name == 'GOAL_SETTING':
        messages.info(request, 'No active check-in quarter')
        return redirect('dashboard')
    
    if request.method == 'POST':
        for goal in goals:
            actual_value = request.POST.get(f'actual_{goal.id}')
            status_val = request.POST.get(f'status_{goal.id}')
            if actual_value:
                achievement, created = QuarterlyAchievement.objects.get_or_create(
                    goal=goal, quarter=current_quarter,
                    defaults={'updated_by': user}
                )
                if goal.uom_type in ['NUMERIC', 'PERCENTAGE']:
                    achievement.actual_value = float(actual_value) if actual_value else None
                elif goal.uom_type == 'TIMELINE':
                    achievement.actual_date = actual_value if actual_value else None
                else:
                    achievement.actual_value = float(actual_value) if actual_value else None
                achievement.status = status_val
                achievement.updated_by = user
                achievement.save()
                
                # Sync shared goal achievements
                if goal.is_shared and goal.is_primary:
                    for copy in goal.shared_copies.all():
                        copy_achievement, _ = QuarterlyAchievement.objects.get_or_create(
                            goal=copy, quarter=current_quarter
                        )
                        copy_achievement.actual_value = achievement.actual_value
                        copy_achievement.actual_date = achievement.actual_date
                        copy_achievement.status = achievement.status
                        copy_achievement.save()
        
        messages.success(request, 'Quarterly update submitted successfully')
        return redirect('dashboard')
    
    achievements = {}
    for goal in goals:
        ach = QuarterlyAchievement.objects.filter(goal=goal, quarter=current_quarter).first()
        achievements[goal.id] = ach
    
    return render(request, 'goals/quarterly_update.html', {
        'goals': goals,
        'achievements': achievements,
        'quarter': current_quarter,
    })

@login_required
@role_required(['MANAGER'])
def team_checkins(request):
    subordinates = request.user.subordinates.all()
    current_quarter = QuarterPeriod.objects.filter(is_active=True).first()
    
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        comment = request.POST.get('comment')
        employee = get_object_or_404(User, id=employee_id)
        
        checkin, created = ManagerCheckIn.objects.get_or_create(
            employee=employee, manager=request.user, quarter=current_quarter,
            defaults={'comment': comment}
        )
        if not created:
            checkin.comment = comment
            checkin.save()
        
        messages.success(request, f'Check-in completed for {employee.username}')
        return redirect('team_checkins')
    
    team_data = []
    for employee in subordinates:
        goals = Goal.objects.filter(owner=employee, status='APPROVED')
        checkin = ManagerCheckIn.objects.filter(employee=employee, manager=request.user, quarter=current_quarter).first()
        
        goal_data = []
        for goal in goals:
            achievement = QuarterlyAchievement.objects.filter(goal=goal, quarter=current_quarter).first()
            goal_data.append({
                'goal': goal,
                'achievement': achievement,
                'progress': goal.get_progress(),
            })
        
        team_data.append({
            'employee': employee,
            'goals': goal_data,
            'checkin': checkin,
            'total_progress': sum(g.calculate_score() for g in goals),
        })
    
    return render(request, 'goals/team_checkins.html', {
        'team_data': team_data,
        'quarter': current_quarter,
    })

@login_required
@role_required(['ADMIN', 'MANAGER'])
def create_shared_goal(request):
    if request.method == 'POST':
        form = SharedGoalForm(request.POST)
        if form.is_valid():
            shared_goal = form.save(commit=False)
            shared_goal.created_by = request.user
            shared_goal.save()
            
            messages.success(request, 'Shared goal created. Now assign to employees.')
            return redirect('assign_shared_goal', shared_goal_id=shared_goal.id)
    else:
        form = SharedGoalForm()
    
    return render(request, 'goals/create_shared_goal.html', {'form': form})

@login_required
@role_required(['ADMIN', 'MANAGER'])
def assign_shared_goal(request, shared_goal_id):
    shared_goal = get_object_or_404(SharedGoalDefinition, id=shared_goal_id)
    employees = User.objects.filter(role='EMPLOYEE')
    
    if request.method == 'POST':
        form = BulkAssignForm(request.POST)
        if form.is_valid():
            selected_employees = form.cleaned_data['employees']
            weightage = form.cleaned_data['weightage']
            
            for employee in selected_employees:
                # Create goal for each employee
                goal = Goal.objects.create(
                    owner=employee,
                    thrust_area=shared_goal.thrust_area,
                    title=shared_goal.title,
                    description=shared_goal.description,
                    uom_type=shared_goal.uom_type,
                    uom_direction=shared_goal.uom_direction,
                    target_value=shared_goal.target_value,
                    weightage=weightage,
                    is_shared=True,
                    status='PENDING'
                )
                
                # Mark primary owner
                if employee == shared_goal.primary_owner:
                    goal.is_primary = True
                    goal.save()
                
                SharedGoalAssignment.objects.create(
                    shared_goal=shared_goal,
                    employee=employee,
                    weightage=weightage,
                    goal=goal
                )
            
            messages.success(request, f'Shared goal assigned to {len(selected_employees)} employees')
            return redirect('dashboard')
    else:
        form = BulkAssignForm()
    
    return render(request, 'goals/assign_shared_goal.html', {
        'shared_goal': shared_goal,
        'form': form,
        'employees': employees,
    })

@login_required
def achievement_report(request):
    if request.user.role == 'ADMIN':
        goals = Goal.objects.filter(status='APPROVED')
        employees = User.objects.filter(role='EMPLOYEE')
    elif request.user.role == 'MANAGER':
        subordinates = request.user.subordinates.all()
        goals = Goal.objects.filter(owner__in=subordinates, status='APPROVED')
        employees = subordinates
    else:
        goals = Goal.objects.filter(owner=request.user, status='APPROVED')
        employees = [request.user]
    
    report_data = []
    for employee in employees:
        emp_goals = goals.filter(owner=employee)
        for goal in emp_goals:
            latest_achievement = goal.achievements.order_by('-quarter__start_date').first()
            report_data.append({
                'employee': employee.username,
                'goal': goal.title,
                'target': goal.target_value if goal.target_value else goal.target_date,
                'actual': latest_achievement.actual_value if latest_achievement else 'Not updated',
                'progress': f"{goal.get_progress():.1f}%",
                'status': latest_achievement.status if latest_achievement else 'Pending',
            })
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="achievement_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Employee', 'Goal', 'Target', 'Actual', 'Progress', 'Status'])
        for row in report_data:
            writer.writerow([row['employee'], row['goal'], row['target'], row['actual'], row['progress'], row['status']])
        return response
    
    return render(request, 'goals/report.html', {'report_data': report_data})

@login_required
def completion_dashboard(request):
    if request.user.role not in ['ADMIN', 'MANAGER']:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    if request.user.role == 'ADMIN':
        employees = User.objects.filter(role='EMPLOYEE')
        managers = User.objects.filter(role='MANAGER')
    else:
        employees = request.user.subordinates.all()
        managers = [request.user]
    
    current_quarter = QuarterPeriod.objects.filter(is_active=True).first()
    
    employee_status = []
    for emp in employees:
        checkin = ManagerCheckIn.objects.filter(employee=emp, quarter=current_quarter).first()
        employee_status.append({
            'employee': emp,
            'has_checkin': checkin is not None,
            'goals_submitted': Goal.objects.filter(owner=emp, status='APPROVED').exists(),
        })
    
    manager_status = []
    for mgr in managers:
        checkins_done = ManagerCheckIn.objects.filter(manager=mgr, quarter=current_quarter).count()
        total_team = mgr.subordinates.count()
        manager_status.append({
            'manager': mgr,
            'checkins_completed': checkins_done,
            'total_team': total_team,
            'completion_rate': (checkins_done / total_team * 100) if total_team > 0 else 0,
        })
    
    return render(request, 'goals/completion_dashboard.html', {
        'employee_status': employee_status,
        'manager_status': manager_status,
        'quarter': current_quarter,
    })
from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect('login')
@login_required
def change_theme(request):
    if request.method == 'POST':
        theme = request.POST.get('theme')
        user = request.user
        if theme in user.unlocked_themes:
            user.theme_preference = theme
            user.save()
            messages.success(request, f'Theme changed to {theme}')
        else:
            messages.error(request, 'Theme not unlocked yet')
    return redirect('dashboard')

@login_required
def audit_log_view(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    logs = AuditLog.objects.all().order_by('-timestamp')[:100]
    return render(request, 'goals/audit_log.html', {'logs': logs})

@login_required
def analytics_view(request):
    if request.user.role not in ['ADMIN', 'MANAGER']:
        return redirect('dashboard')
    
    # QoQ trends
    quarters = QuarterPeriod.objects.exclude(name='GOAL_SETTING').order_by('start_date')[:4]
    trends = []
    for q in quarters:
        achievements = QuarterlyAchievement.objects.filter(quarter=q)
        avg_progress = achievements.aggregate(Avg('actual_value'))['actual_value__avg'] or 0
        trends.append({'quarter': q.name, 'progress': avg_progress})
    
    # Goal distribution
    thrust_distribution = Goal.objects.values('thrust_area').annotate(count=models.Count('id'))
    
    context = {
        'trends': trends,
        'thrust_distribution': list(thrust_distribution),
    }
    return render(request, 'goals/analytics.html', context)
