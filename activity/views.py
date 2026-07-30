from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db import connection
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import timedelta
import json

User = get_user_model()


def table_exists():
    return 'activity_activitylog' in connection.introspection.table_names()


def parse_user_agent(ua_string):
    try:
        from user_agents import parse
        ua = parse(ua_string)
        browser = f"{ua.browser.family} {ua.browser.version_string}" if ua.browser.family != 'Other' else 'Unknown Browser'
        os_name = f"{ua.os.family} {ua.os.version_string}" if ua.os.family != 'Other' else 'Unknown OS'
        device = ua.device.family if ua.device.family != 'Other' else 'Desktop'
        if ua.is_mobile:
            device = 'Mobile'
        elif ua.is_tablet:
            device = 'Tablet'
        elif ua.is_pc:
            device = 'Desktop'
        return browser, os_name, device
    except Exception:
        return 'Unknown Browser', 'Unknown OS', 'Unknown'


def get_active_sessions():
    active_sessions = []
    now = timezone.now()
    sessions = Session.objects.filter(expire_date__gte=now)

    for session in sessions:
        try:
            data = session.get_decoded()
            user_id = data.get('_auth_user_id')
            if user_id:
                try:
                    user = User.objects.get(pk=user_id)
                except User.DoesNotExist:
                    continue

                ip = data.get('ip_address', 'Unknown')
                user_agent_str = data.get('user_agent', '')
                login_time_str = data.get('login_time', '')

                login_time_display = '-'
                if login_time_str:
                    try:
                        from datetime import datetime
                        lt = datetime.fromisoformat(login_time_str)
                        if timezone.is_naive(lt):
                            lt = timezone.make_aware(lt)
                        lt_pakistan = timezone.localtime(tz=timezone.get_current_timezone())
                        lt_pakistan = lt.astimezone(timezone.get_current_timezone())
                        login_time_display = lt_pakistan.strftime('%b %d, %Y %I:%M %p')
                    except Exception:
                        login_time_display = login_time_str

                browser, os_name, device = parse_user_agent(user_agent_str)

                active_sessions.append({
                    'user': user,
                    'session_key': session.session_key,
                    'ip': ip,
                    'browser': browser,
                    'os': os_name,
                    'device': device,
                    'login_time': login_time_display,
                    'last_activity': session.expire_date,
                })
        except Exception:
            continue

    return active_sessions


@login_required(login_url='/admin/login/')
def activity_dashboard(request):
    if not request.user.is_superuser:
        return redirect('admin_login')

    active_users = get_active_sessions()

    activities = []
    stats = []
    user_stats = []
    all_users = []

    if table_exists():
        from .models import ActivityLog

        days = int(request.GET.get('days', 7))
        user_id = request.GET.get('user')
        action_filter = request.GET.get('action')

        start_date = timezone.now() - timedelta(days=days)

        activities_qs = ActivityLog.objects.filter(
            timestamp__gte=start_date
        ).select_related('user')

        if user_id:
            activities_qs = activities_qs.filter(user_id=user_id)
        if action_filter:
            activities_qs = activities_qs.filter(action=action_filter)

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

        activities = activities_qs[:100]
        all_users = ActivityLog.objects.filter(
            user__isnull=False
        ).values('user__id', 'user__username').distinct()

    context = {
        'activities': activities,
        'stats': stats,
        'user_stats': user_stats,
        'all_users': all_users,
        'selected_days': int(request.GET.get('days', 7)),
        'selected_user': request.GET.get('user'),
        'selected_action': request.GET.get('action'),
        'action_choices': ActivityLog.ACTION_CHOICES if table_exists() else [],
        'active_users': active_users,
    }

    return render(request, 'activity/activity_dashboard.html', context)


@require_POST
@login_required(login_url='/admin/login/')
def force_logout(request, session_key):
    if not request.user.is_superuser:
        return redirect('admin_login')

    try:
        session = Session.objects.get(session_key=session_key)
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')

        if user_id and int(user_id) != request.user.id:
            session.delete()

        if table_exists():
            from .models import ActivityLog
            try:
                target_user = User.objects.get(pk=user_id)
                ActivityLog.objects.create(
                    user=request.user,
                    action='FORCE_LOGOUT',
                    details={
                        'target_user': target_user.username,
                        'session_key': session_key,
                    }
                )
            except User.DoesNotExist:
                pass

        return JsonResponse({'status': 'ok', 'message': 'User logged out successfully'})
    except Session.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Session not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
