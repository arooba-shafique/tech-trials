from django import forms
from django.contrib.auth import get_user_model
from .models import AdminManager

User = get_user_model()

class AdminManagerForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank when editing to keep current password."
    )
    email = forms.EmailField(required=False)

    class Meta:
        model  = AdminManager
        fields = [
            'full_name', 'phone', 'employee_id',
            'can_manage_students', 'can_manage_teachers', 'can_manage_classes',
            'can_manage_hr_attendance',
        ]

    def __init__(self, *args, **kwargs):
        self.instance_user = kwargs.pop('instance_user', None)
        super().__init__(*args, **kwargs)
        if self.instance_user:
            self.fields['username'].initial = self.instance_user.username
            self.fields['email'].initial    = self.instance_user.email

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username=username)
        if self.instance_user:
            qs = qs.exclude(pk=self.instance_user.pk)
        if qs.exists():
            raise forms.ValidationError("This username is already taken.")
        return username