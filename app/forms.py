from django import forms
from .models import Goal, SharedGoalDefinition, User
from django.conf import settings

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['thrust_area', 'title', 'description', 'uom_type', 'uom_direction', 'target_value', 'target_date', 'weightage']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_weightage(self):
        weightage = self.cleaned_data.get('weightage')
        if weightage < 10:
            raise forms.ValidationError('Minimum weightage per goal is 10%')
        return weightage

class GoalApprovalForm(forms.Form):
    weightage = forms.FloatField(min_value=10, max_value=100, required=False)
    target_value = forms.FloatField(required=False)

class QuarterlyAchievementForm(forms.Form):
    actual_value = forms.FloatField(required=False)
    status = forms.ChoiceField(choices=settings.GOAL_STATUS)

class SharedGoalForm(forms.ModelForm):
    class Meta:
        model = SharedGoalDefinition
        fields = ['title', 'description', 'thrust_area', 'target_value', 'uom_type', 'uom_direction', 'primary_owner']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class BulkAssignForm(forms.Form):
    employees = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='EMPLOYEE'),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    weightage = forms.FloatField(min_value=10, max_value=100, initial=20)
