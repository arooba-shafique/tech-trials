from django.db import connection


EXEMPT_PATHS = [
    '/static/',
    '/media/',
    '/admin/jsi18n/',
    '/activity/log/',
]


class ActivityTrackingMiddleware:
    """Middleware to track user page visits."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            if request.user.is_authenticated and request.method == 'GET':
                path = request.path

                if not any(path.startswith(p) for p in EXEMPT_PATHS):
                        if 'activity_activitylog' in connection.introspection.table_names():
                            from .models import ActivityLog
                            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                            x_real_ip = request.META.get('HTTP_X_REAL_IP')
                            if x_forwarded_for:
                                ip = x_forwarded_for.split(',')[0].strip()
                            elif x_real_ip:
                                ip = x_real_ip
                            else:
                                ip = request.META.get('REMOTE_ADDR')

                        ActivityLog.objects.create(
                            user=request.user,
                            action='PAGE_VISIT',
                            ip_address=ip,
                            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                            path=path,
                            method=request.method,
                        )
        except Exception:
            pass

        return response
