from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()


def table_exists():
    return 'activity_activitylog' in connection.introspection.table_names()


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    elif x_real_ip:
        return x_real_ip
    return request.META.get('REMOTE_ADDR')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    try:
        if table_exists():
            from .models import ActivityLog
            ActivityLog.objects.create(
                user=user,
                action='LOGIN',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                path=request.path,
                method=request.method,
                details={'login_backend': str(kwargs.get('backend', ''))}
            )
    except Exception:
        pass


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    try:
        if user and user.is_authenticated and table_exists():
            from .models import ActivityLog
            ActivityLog.objects.create(
                user=user,
                action='LOGOUT',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                path=request.path,
                method=request.method,
            )
    except Exception:
        pass


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    try:
        if table_exists():
            from .models import ActivityLog
            username = credentials.get('username', 'Unknown') if credentials else 'Unknown'
            ActivityLog.objects.create(
                action='LOGIN_FAILED',
                ip_address=get_client_ip(request) if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
                path=request.path if request else None,
                method=request.method if request else None,
                details={'attempted_username': username}
            )
    except Exception:
        pass


def log_model_change(user, action, instance, old_values=None, new_values=None, request=None):
    try:
        if table_exists():
            from .models import ActivityLog
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
    except Exception:
        pass
