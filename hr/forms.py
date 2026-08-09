import calendar
from django import forms
from .models import EmployeeSalary, MonthlySalary, SalaryConfig, EmployeeAttendance, SeparationRecord


class EmployeeSalaryForm(forms.ModelForm):
    class Meta:
        model = EmployeeSalary
        fields = [
            'employee', 'basic_salary', 'salary_type', 'employment_type',
            'working_days_per_week', 'bank_account', 'bank_name',
            'housing_allowance', 'medical_allowance', 'transport_allowance',
            'kid_fee', 'other_allowance',
        ]


class MonthlySalaryForm(forms.ModelForm):
    class Meta:
        model = MonthlySalary
        fields = [
            'employee', 'month', 'year', 'total_working_days',
            'days_present', 'days_absent', 'allowed_leaves', 'late_coming_days',
            'increment', 'advance_deduction', 'provident_fund',
            'security_deduction', 'other_deduction', 'bonus_per_day',
            'remarks',
        ]
        widgets = {
            'month': forms.Select(choices=[(i, calendar.month_name[i]) for i in range(1, 13)]),
        }


class SalaryConfigForm(forms.ModelForm):
    class Meta:
        model = SalaryConfig
        fields = ['tax_percentage']


class EmployeeAttendanceForm(forms.ModelForm):
    class Meta:
        model = EmployeeAttendance
        fields = ['employee', 'date', 'status', 'check_in', 'check_out', 'remarks']


class GenerateSalaryForm(forms.Form):
    month = forms.ChoiceField(
        choices=[(i, calendar.month_name[i]) for i in range(1, 13)],
        label='Month'
    )
    year = forms.IntegerField(min_value=2020, max_value=2030, initial=2026, label='Year')
    total_working_days = forms.IntegerField(min_value=1, max_value=31, initial=26, label='Total Working Days')
    bonus_per_day = forms.DecimalField(max_digits=12, decimal_places=2, initial=0, label='Bonus Per Day (if 0 leaves)', required=False)


class SeparationForm(forms.ModelForm):
    class Meta:
        model = SeparationRecord
        fields = ['last_working_date', 'separation_reason', 'separation_reason_detail', 'notes']
        widgets = {
            'last_working_date': forms.DateInput(attrs={'type': 'date'}),
            'separation_reason_detail': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ClearanceForm(forms.ModelForm):
    class Meta:
        model = SeparationRecord
        fields = [
            'security_deduction', 'last_salary_withheld', 'last_salary_amount',
            'additional_deductions', 'deduction_reason',
            'clearance_status', 'clearance_date', 'notes',
        ]
        widgets = {
            'clearance_date': forms.DateInput(attrs={'type': 'date'}),
            'deduction_reason': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
