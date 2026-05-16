from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from app.models import User, QuarterPeriod
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Setup demo data for GoalQuest Portal'

    def handle(self, *args, **kwargs):
        # Create demo users
        admin = User.objects.create(
            username='admin',
            email='admin@goalquest.com',
            password=make_password('admin123'),
            role='ADMIN',
            first_name='Admin',
            last_name='User'
        )
        
        manager = User.objects.create(
            username='manager',
            email='manager@goalquest.com',
            password=make_password('manager123'),
            role='MANAGER',
            first_name='John',
            last_name='Manager'
        )
        
        employee1 = User.objects.create(
            username='employee1',
            email='emp1@goalquest.com',
            password=make_password('employee123'),
            role='EMPLOYEE',
            first_name='Alice',
            last_name='Employee',
            manager=manager
        )
        
        employee2 = User.objects.create(
            username='employee2',
            email='emp2@goalquest.com',
            password=make_password('employee123'),
            role='EMPLOYEE',
            first_name='Bob',
            last_name='Worker',
            manager=manager
        )
        
        # Create quarter periods
        year = 2025
        quarters = [
            ('GOAL_SETTING', date(year, 5, 1), date(year, 6, 30)),
            ('Q1', date(year, 7, 1), date(year, 9, 30)),
            ('Q2', date(year, 10, 1), date(year, 12, 31)),
            ('Q3', date(year, 1, 1), date(year, 3, 31)),
            ('Q4', date(year, 3, 1), date(year, 4, 30)),
        ]
        
        for name, start, end in quarters:
            QuarterPeriod.objects.get_or_create(
                name=name,
                year=year,
                defaults={
                    'start_date': start,
                    'end_date': end,
                    'is_active': name == 'Q1'
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))
        self.stdout.write('Login credentials:')
        self.stdout.write('Admin: admin / admin123')
        self.stdout.write('Manager: manager / manager123')
        self.stdout.write('Employee: employee1 / employee123')