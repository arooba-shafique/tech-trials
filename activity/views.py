from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db import connection
from django.utils import timezone
from datetime import timedelta


def table_exists():
    return 'activity_activitylog' in connection.introspection.table_names()


@login_required(login_url='/admin/login/')
def activity_dashboard(request):
    if not request.user.is_superuser:
        return redirect('admin_login')

    if not table_exists():
        return render(request, 'activity_dashboard.html', {
            'activities': [],
            'stats': [],
            'user_stats': [],
            'all_users': [],
            'selected_days': 7,
            'selected_user': None,
            'selected_action': None,
            'action_choices': [],
            'error': 'Activity log table not found. Migrations may not have run yet.',
        })

    from .models import ActivityLog

    days = int(request.GET.get('days', 7))
    user_id = request.GET.get('user')
    action_filter = request.GET.get('action')

    start_date = timezone.now() - timedelta(days=days)

    activities = ActivityLog.objects.filter(
        timestamp__gte=start_date
    ).select_related('user')

    if user_id:
        activities = activities.filter(user_id=user_id)

    if action_filter:
        activities = activities.filter(action=action_filter)

    stats = ActivityLog.objects.filter(
        timestamp__gte=start_date
    ).values('action').annotate(count=Count('id')).order_by('-count')

    user_stats = ActivityLog.objects.filter(
        timestamp__gte=start_date,
        user__isnull=False
    ).values(
        'user__username', 'user__role'
    ).annotate(
        total=Count('id'),
        logins=Count('id', filter=Q(action='LOGIN')),
        password_changes=Count('id', filter=Q(action='PASSWORD_CHANGED')),
    ).order_by('-total')[:20]

    recent_activities = activities[:100]
    all_users = ActivityLog.objects.filter(
        user__isnull=False
    ).values('user__id', 'user__username').distinct()

    context = {
        'activities': recent_activities,
        'stats': stats,
        'user_stats': user_stats,
        'all_users': all_users,
        'selected_days': days,
        'selected_user': user_id,
        'selected_action': action_filter,
        'action_choices': ActivityLog.ACTION_CHOICES,
    }

    return render(request, 'activity_dashboard.html', context)
