from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from .models import ActivityLog

User = get_user_model()


def get_client_ip(request):
    """Extract IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user login."""
    ActivityLog.objects.create(
        user=user,
        action='LOGIN',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        path=request.path,
        method=request.method,
        details={'login_backend': str(kwargs.get('backend', ''))}
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout."""
    if user and user.is_authenticated:
        ActivityLog.objects.create(
            user=user,
            action='LOGOUT',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            path=request.path,
            method=request.method,
        )


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    """Log failed login attempt."""
    username = credentials.get('username', 'Unknown') if credentials else 'Unknown'
    ActivityLog.objects.create(
        action='LOGIN_FAILED',
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
        path=request.path if request else None,
        method=request.method if request else None,
        details={'attempted_username': username}
    )


def log_model_change(user, action, instance, old_values=None, new_values=None, request=None):
    """Log model create/update/delete operations."""
    details = {}
    if old_values and new_values:
        for field in new_values:
            if field in old_values and old_values[field] != new_values[field]:
                details[field] = {
                    'old': str(old_values[field]),
                    'new': str(new_values[field])
                }

    ActivityLog.objects.create(
        user=user,
        action=action,
        model_name=instance.__class__.__name__,
        object_id=str(instance.pk),
        object_repr=str(instance)[:200],
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
        details=details if details else None,
    )
