from django.contrib.auth.models import AbstractUser
from django.db import models


class School(models.Model):
    name = models.CharField(max_length=200)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Schools"


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('admin_manager', 'Admin Manager'),
        ('principal', 'Principal'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    school = models.ForeignKey(
        School, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='users'
    )

    def __str__(self):
        return f"{self.username} - {self.role}"


class AdminManager(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='admin_manager_profile'
    )
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=30, unique=True, blank=True, null=True)

    can_manage_students = models.BooleanField(default=True)
    can_manage_teachers = models.BooleanField(default=True)
    can_manage_classes  = models.BooleanField(default=True)
    can_manage_hr_attendance = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_attendance_only(self):
        return (
            self.can_manage_hr_attendance
            and not self.can_manage_students
            and not self.can_manage_teachers
            and not self.can_manage_classes
        )

    def __str__(self):
        return self.full_name