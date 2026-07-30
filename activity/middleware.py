from .models import ActivityLog


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

        if request.user.is_authenticated and request.method == 'GET':
            path = request.path

            if not any(path.startswith(p) for p in EXEMPT_PATHS):
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')

                ActivityLog.objects.create(
                    user=request.user,
                    action='PAGE_VISIT',
                    ip_address=ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    path=path,
                    method=request.method,
                )

        return response
