from django import forms
from django.contrib.auth import get_user_model
from .models import AdminManager

User = get_user_model()

ROLE_CHOICES = [
    ('', '— Select Role —'),
    ('full', 'Full Admin Manager'),
    ('attendance', 'Attendance Manager'),
    ('employee_viewer', 'Employee Viewer'),
]

class AdminManagerForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank when editing to keep current password."
    )
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect, required=True)

    class Meta:
        model  = AdminManager
        fields = [
            'full_name', 'phone', 'employee_id',
            'can_manage_students', 'can_manage_teachers', 'can_manage_classes',
            'can_manage_hr_attendance', 'can_view_edit_employees',
        ]

    def __init__(self, *args, **kwargs):
        self.instance_user = kwargs.pop('instance_user', None)
        super().__init__(*args, **kwargs)
        if self.instance_user:
            self.fields['username'].initial = self.instance_user.username
            self.fields['email'].initial    = self.instance_user.email
        if self.instance and self.instance.pk:
            if self.instance.can_manage_students and self.instance.can_manage_teachers and self.instance.can_manage_classes:
                self.fields['role'].initial = 'full'
            elif self.instance.can_manage_hr_attendance:
                self.fields['role'].initial = 'attendance'
            elif self.instance.can_view_edit_employees:
                self.fields['role'].initial = 'employee_viewer'

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username=username)
        if self.instance_user:
            qs = qs.exclude(pk=self.instance_user.pk)
        if qs.exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        role = self.cleaned_data.get('role', '')
        self.instance.can_manage_students = role == 'full'
        self.instance.can_manage_teachers = role == 'full'
        self.instance.can_manage_classes = role == 'full'
        self.instance.can_manage_hr_attendance = role == 'attendance'
        self.instance.can_view_edit_employees = role == 'employee_viewer'
        return super().save(commit=commit)