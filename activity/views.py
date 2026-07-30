from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import ActivityLog


@staff_member_required
def activity_dashboard(request):
    """Activity tracking dashboard for superusers."""
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
