from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .models import (
    HomeTask,  # <--- Make sure this is here
    StudentProfile,
    TimetableSlot,
    TeacherProfile,
    ParentProfile,
    Class,
    Subject,
    TeacherSubjectAssignment,
    Exam,
    Result,
    Attendance
)

from .forms import (
    StudentProfileForm,
    TeacherProfileForm,
    ParentProfileForm,
    ClassForm,
    SubjectForm,
    TeacherSubjectAssignmentForm
)


def get_user_school(user):
    return getattr(user, 'school', None)


# ─────────────────────────────────────────────
# ATTENDANCE-ONLY ADMIN MANAGER DASHBOARD
# ─────────────────────────────────────────────

def _attendance_only_dashboard(request, today):
    """Minimal dashboard for attendance-only admin managers — HR monthly attendance only."""
    school = get_user_school(request.user)

    from django.db.models import Q
    if not request.user.is_superuser and school:
        teachers_qs = TeacherProfile.objects.filter(Q(school=school) | Q(school__isnull=True), is_employee_separated=False).select_related('salary_detail')
    else:
        teachers_qs = TeacherProfile.objects.filter(is_employee_separated=False).select_related('salary_detail')

    import calendar
    from hr.models import SalaryConfig, MonthlySalary

    att_month = int(request.GET.get('month', today.month)) if request.GET.get('month') and request.GET.get('section') == 'hr-attendance' else today.month
    att_year = int(request.GET.get('year', today.year)) if request.GET.get('year') and request.GET.get('section') == 'hr-attendance' else today.year
    att_config = SalaryConfig.objects.filter(month=att_month, year=att_year).first()
    att_working_days = att_config.default_working_days if att_config else 26
    att_days_in_month = calendar.monthrange(att_year, att_month)[1]

    hr_attendance_employees = teachers_qs.filter(is_employee_separated=False)
    hr_att_existing = {}
    for ms in MonthlySalary.objects.filter(month=att_month, year=att_year, employee__in=hr_attendance_employees):
        ms.days_present = max(0, att_days_in_month - ms.days_absent)
        hr_att_existing[ms.employee_id] = ms

    hr_months = [(i, calendar.month_name[i]) for i in range(1, 13)]

    # Count how many employees have attendance saved this month
    saved_count = MonthlySalary.objects.filter(month=att_month, year=att_year).exclude(days_absent=0, paid_leaves=0, unpaid_leaves=0, late_coming_days=0).count()

    context = {
        'teachers': teachers_qs,
        'hr_attendance_employees': hr_attendance_employees,
        'hr_att_existing': hr_att_existing,
        'hr_att_total_working_days': att_working_days,
        'hr_months': hr_months,
        'att_month': att_month,
        'att_year': att_year,
        'att_month_name': calendar.month_name[att_month],
        'att_days_in_month': att_days_in_month,
        'user_role': 'admin_manager',
        'total_employees': teachers_qs.count(),
        'saved_attendance_count': saved_count,
    }

    return render(request, 'admin_manager_attendance_only.html', context)


# ─────────────────────────────────────────────
# EMPLOYEE VIEWER ADMIN MANAGER DASHBOARD
# ─────────────────────────────────────────────

def _employee_viewer_dashboard(request, today):
    """Dashboard for employee-viewer admin managers — view/edit staff info only, no salary access."""
    school = get_user_school(request.user)

    from django.db.models import Q
    if not request.user.is_superuser and school:
        teachers_qs = TeacherProfile.objects.filter(Q(school=school) | Q(school__isnull=True), is_employee_separated=False).select_related('salary_detail')
    else:
        teachers_qs = TeacherProfile.objects.filter(is_employee_separated=False).select_related('salary_detail')

    context = {
        'teachers': teachers_qs,
        'user_role': 'admin_manager',
    }

    return render(request, 'admin_manager_employee_viewer.html', context)


# ─────────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────────

@login_required(login_url='admin_login')
def admin_dashboard(request):
    role = getattr(request.user, 'role', None)

    if not (request.user.is_authenticated and role in ("admin_manager", "principal")):
        return HttpResponse("Unauthorized Access", status=403)

    school = get_user_school(request.user)
    today = timezone.now().date()

    # Check if this admin_manager is attendance-only
    is_attendance_only = False
    is_employee_viewer = False
    if role == 'admin_manager':
        from accounts.models import AdminManager
        try:
            profile = request.user.admin_manager_profile
            is_attendance_only = profile.is_attendance_only
            is_employee_viewer = profile.is_employee_viewer
        except AdminManager.DoesNotExist:
            pass

    if is_attendance_only:
        return _attendance_only_dashboard(request, today)

    if is_employee_viewer:
        return _employee_viewer_dashboard(request, today)

    from django.db.models import Q

    school_filter = {}
    if not request.user.is_superuser and school:
        school_filter = {'school': school}

    students_qs = StudentProfile.objects.filter(**school_filter)
    if not request.user.is_superuser and school:
        teachers_qs = TeacherProfile.objects.filter(Q(school=school) | Q(school__isnull=True), is_employee_separated=False).select_related('salary_detail')
    else:
        teachers_qs = TeacherProfile.objects.filter(is_employee_separated=False).select_related('salary_detail')
    parents_qs = ParentProfile.objects.filter(**school_filter)
    classes_qs = Class.objects.filter(**school_filter)
    subjects_qs = Subject.objects.filter(**school_filter)

    all_results = Result.objects.filter(
        student__in=students_qs
    ).select_related(
        'student__student_class', 'exam'
    ).order_by('student__student_class__name')

    classes = classes_qs

    for cls in classes:
        cls.total_students = students_qs.filter(student_class=cls).count()
        cls_results = [r for r in all_results if r.student.student_class_id == cls.id]
        cls.pass_count = sum(1 for r in cls_results if getattr(r, "is_passing", False))
        cls.fail_count = sum(1 for r in cls_results if not getattr(r, "is_passing", False))

    assignments_qs = TeacherSubjectAssignment.objects.filter(
        assigned_class__in=classes_qs
    ) if not request.user.is_superuser else TeacherSubjectAssignment.objects.all()

    User = get_user_model()

    from django.db.models import Q as Q2
    from hr.models import MonthlySalary, SeparationRecord
    left_employees = TeacherProfile.objects.filter(is_employee_separated=True)
    if school and not request.user.is_superuser:
        left_employees = left_employees.filter(Q(school=school) | Q(school__isnull=True))
    left_search = request.GET.get('search', '').strip() if request.GET.get('section') == 'left-employees' else ''
    if left_search:
        left_employees = left_employees.filter(
            Q2(full_name__icontains=left_search) |
            Q2(employee_id__icontains=left_search) |
            Q2(cnic__icontains=left_search)
        )
    left_employees = left_employees.order_by('-id')

    left_data = []
    left_pending_count = 0
    left_completed_count = 0
    pending_clearance_alerts = []
    for emp in left_employees:
        sep = SeparationRecord.objects.filter(employee=emp).first()
        if sep:
            if sep.clearance_status == 'completed':
                left_completed_count += 1
            else:
                left_pending_count += 1
                # Check if 3+ months have passed since leaving
                if sep.last_working_date:
                    months_passed = (today.year - sep.last_working_date.year) * 12 + (today.month - sep.last_working_date.month)
                    if months_passed >= 3:
                        pending_clearance_alerts.append({
                            'employee': emp,
                            'separation': sep,
                            'months_passed': months_passed,
                        })
        else:
            left_pending_count += 1

        last_salary = None
        if sep and sep.last_working_date:
            last_salary = MonthlySalary.objects.filter(
                employee=emp
            ).filter(
                Q2(year__lt=sep.last_working_date.year) |
                Q2(year=sep.last_working_date.year, month__lte=sep.last_working_date.month)
            ).order_by('-year', '-month').first()

        left_data.append({
            'employee': emp,
            'separation': sep,
            'last_salary': last_salary,
        })

    context = {
        'students':      students_qs,
        'teachers':      teachers_qs,
        'parents':       parents_qs,
        'classes':       classes,
        'subjects':      subjects_qs,
        'assignments':   assignments_qs,
        'exams':         Exam.objects.filter(assigned_class__in=classes_qs) if not request.user.is_superuser else Exam.objects.all(),
        'results':       all_results,
        'attendance':    Attendance.objects.filter(student__in=students_qs).order_by('-date')[:50] if not request.user.is_superuser else Attendance.objects.order_by('-date')[:50],
        'present_today': Attendance.objects.filter(student__in=students_qs, date=today, status='present').values('student').distinct().count() if not request.user.is_superuser else Attendance.objects.filter(date=today, status='present').values('student').distinct().count(),
        'absent_today':  Attendance.objects.filter(student__in=students_qs, date=today, status='absent').values('student').distinct().count() if not request.user.is_superuser else Attendance.objects.filter(date=today, status='absent').values('student').distinct().count(),
        'leave_today':   Attendance.objects.filter(student__in=students_qs, date=today, status='leave').values('student').distinct().count() if not request.user.is_superuser else Attendance.objects.filter(date=today, status='leave').values('student').distinct().count(),
        'user_role':     role,
        'admin_users':   User.objects.filter(role__in=['admin', 'admin_manager'], school=school).order_by('role', 'username') if not request.user.is_superuser else User.objects.filter(role__in=['admin', 'admin_manager']).order_by('role', 'username'),
        'left_data': left_data,
        'left_pending_count': left_pending_count,
        'left_completed_count': left_completed_count,
        'left_search': left_search,
        'pending_clearance_alerts': pending_clearance_alerts,
    }

    # Add HR data for admin_manager
    if role in ('admin_manager', 'principal'):
        try:
            from hr.models import SalaryConfig, MonthlySalary, EmployeeAttendance
            import calendar
            current_month = today.month
            current_year = today.year

            # Salary sheet month/year from GET params
            sheet_month = int(request.GET.get('month', today.month)) if request.GET.get('month') else today.month
            sheet_year = int(request.GET.get('year', today.year)) if request.GET.get('year') else today.year

            hr_config = SalaryConfig.objects.filter(month=sheet_month, year=sheet_year).first()
            if not hr_config:
                class _DefaultConfig:
                    month = sheet_month
                    year = sheet_year
                    default_working_days = 26
                    max_allowed_leaves = 0
                    late_deduction_per = 3
                    housing_allowance_pct = 0
                    medical_allowance_pct = 0
                    transport_allowance_pct = 0
                    fuel_allowance_pct = 0
                    tax_percentage = 0
                    provident_fund_pct = 0
                    security_pct = 0
                    van_child_pct = 0
                    bonus_per_day = 0
                    bonus_percentage = 0
                    config_mode = 'percentage'
                hr_config = _DefaultConfig()

            hr_salaries = MonthlySalary.objects.filter(month=sheet_month, year=sheet_year).select_related('employee')
            hr_month_name = calendar.month_name[sheet_month]
            hr_months = [(i, calendar.month_name[i]) for i in range(1, 13)]

            # All employees for salary slips dropdown
            hr_all_employees = teachers_qs.filter(is_employee_separated=False).order_by('full_name')

            # Salary slips
            slip_selected_employee = request.GET.get('employee_id', '')
            slip_salaries = MonthlySalary.objects.filter(month=sheet_month, year=sheet_year).select_related('employee')
            slip_selected_name = ''

            # Monthly attendance data
            att_month = int(request.GET.get('month', today.month)) if request.GET.get('month') and request.GET.get('section') == 'hr-attendance' else today.month
            att_year = int(request.GET.get('year', today.year)) if request.GET.get('year') and request.GET.get('section') == 'hr-attendance' else today.year
            att_config = SalaryConfig.objects.filter(month=att_month, year=att_year).first()
            att_working_days = att_config.default_working_days if att_config else 26
            att_days_in_month = calendar.monthrange(att_year, att_month)[1]

            hr_attendance_employees = teachers_qs.filter(is_employee_separated=False)
            hr_att_existing = {}
            for ms in MonthlySalary.objects.filter(month=att_month, year=att_year, employee__in=hr_attendance_employees):
                # Recalculate days_present using natural calendar days (only absent days reduce it)
                ms.days_present = max(0, att_days_in_month - ms.days_absent)
                hr_att_existing[ms.employee_id] = ms

            # Pre-compute display values for per-employee override table (from MonthlySalary)
            ms_lookup = {}
            try:
                for ms in MonthlySalary.objects.filter(month=sheet_month, year=sheet_year, employee__in=teachers_qs):
                    ms_lookup[ms.employee_id] = ms
            except Exception:
                pass

            for teacher in teachers_qs:
                # Determine if employee is in first 2 months
                from datetime import date
                teacher.is_new_employee = False
                if teacher.joining_date:
                    salary_date = date(sheet_year, sheet_month, 1)
                    months_since = (salary_date.year - teacher.joining_date.year) * 12 + (salary_date.month - teacher.joining_date.month)
                    if months_since < 2:
                        teacher.is_new_employee = True

                ms = ms_lookup.get(teacher.id)
                has_cfg = False
                if ms:
                    try:
                        has_cfg = any([ms.cfg_housing_pct, ms.cfg_medical_pct, ms.cfg_transport_pct,
                                      ms.cfg_kid_fee_pct, ms.cfg_tax_pct, ms.cfg_pf_pct,
                                      ms.cfg_security_pct, ms.cfg_van_child_pct,
                                      ms.cfg_bonus_per_day, ms.cfg_bonus_pct])
                    except Exception:
                        pass
                if has_cfg:
                    try:
                        teacher.ov_housing = float(ms.cfg_housing_pct)
                        teacher.ov_medical = float(ms.cfg_medical_pct)
                        teacher.ov_transport = float(ms.cfg_transport_pct)
                        teacher.ov_kid_fee = float(ms.cfg_kid_fee_pct)
                        teacher.ov_tax = float(ms.cfg_tax_pct)
                        teacher.ov_pf = float(ms.cfg_pf_pct)
                        teacher.ov_security = float(ms.cfg_security_pct)
                        teacher.ov_van_child = float(ms.cfg_van_child_pct)
                        teacher.ov_bonus_per_day = float(ms.cfg_bonus_per_day)
                        teacher.ov_bonus_pct = float(ms.cfg_bonus_pct)
                        teacher.ov_transaction_type = ms.transaction_type or 'bank_islami'
                        teacher.ov_active = True
                    except Exception:
                        teacher.ov_housing = 0
                        teacher.ov_medical = 0
                        teacher.ov_transport = 0
                        teacher.ov_kid_fee = 0
                        teacher.ov_tax = 0
                        teacher.ov_pf = 0
                        teacher.ov_security = 0
                        teacher.ov_van_child = 0
                        teacher.ov_bonus_per_day = 0
                        teacher.ov_bonus_pct = 0
                        teacher.ov_active = False
                        teacher.ov_transaction_type = 'bank_islami'
                else:
                    teacher.ov_housing = 0
                    teacher.ov_medical = 0
                    teacher.ov_transport = 0
                    teacher.ov_kid_fee = 0
                    teacher.ov_tax = 0
                    teacher.ov_pf = 0
                    teacher.ov_security = 0
                    teacher.ov_van_child = 0
                    teacher.ov_bonus_per_day = 0
                    teacher.ov_bonus_pct = 0
                    teacher.ov_active = False
                    teacher.ov_transaction_type = 'bank_islami'

            context.update({
                'hr_config': hr_config,
                'hr_salaries': list(hr_salaries),
                'hr_month': sheet_month,
                'hr_year': sheet_year,
                'hr_month_name': hr_month_name,
                'hr_months': hr_months,
                'hr_total_gross': sum(s.gross_salary for s in hr_salaries),
                'hr_total_basic': sum(s.basic_salary for s in hr_salaries),
                'hr_total_deductions': sum(s.total_deductions for s in hr_salaries),
                'hr_total_net': sum(s.net_salary for s in hr_salaries),
                'hr_attendance_employees': hr_attendance_employees,
                'hr_att_existing': hr_att_existing,
                'hr_att_total_working_days': att_working_days,
                'hr_all_employees': hr_all_employees,
                'slip_salaries': slip_salaries,
                'slip_selected_employee': slip_selected_employee,
                'slip_selected_name': slip_selected_name,
                'current_month': current_month,
                'current_year': current_year,
                'current_month_name': calendar.month_name[current_month],
                'att_month': att_month,
                'att_year': att_year,
                'att_month_name': calendar.month_name[att_month],
                'att_days_in_month': att_days_in_month,
            })
        except Exception as e:
            import traceback
            traceback.print_exc()

    template = 'admin_manager_dashboard.html' if role == 'admin_manager' else 'admin_dashboard.html'
    return render(request, template, context)


# ─────────────────────────────────────────────
# SECTION TAG MAP
# ─────────────────────────────────────────────

SECTION_TAGS = {
    'Student':            'students',
    'Teacher':            'staff',
    'Parent':             'parents',
    'Class':              'classes',
    'Subject':            'subjects',
    'Teacher Assignment': 'assignments',
    'Assignment':         'assignments',
}


# ─────────────────────────────────────────────
# GENERIC ADD / EDIT / DELETE
# ─────────────────────────────────────────────

@login_required(login_url='admin_login')
def add_model_entry(request, form_class, model_name, template_name):
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            tag = SECTION_TAGS.get(model_name, 'dashboard')
            messages.success(request, f'{model_name} added successfully.', extra_tags=tag)
            return redirect('admin_console')
    else:
        form = form_class()
    return render(request, template_name, {'form': form, 'model_name': model_name})


@login_required(login_url='admin_login')
def edit_model_entry(request, instance, form_class, model_name, template_name):
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            tag = SECTION_TAGS.get(model_name, 'dashboard')
            messages.success(request, f'{model_name} updated successfully.', extra_tags=tag)
            return redirect('admin_console')
    else:
        form = form_class(instance=instance)
    return render(request, template_name, {'form': form, 'model_name': model_name, 'edit': True})


@login_required(login_url='admin_login')
def delete_model_entry(request, instance, model_name):
    if request.method == 'POST':
        instance.delete()
        tag = SECTION_TAGS.get(model_name, 'dashboard')
        messages.success(request, f'{model_name} deleted successfully.', extra_tags=tag)
    return redirect('admin_console')


from django.contrib.auth import get_user_model


def _save_email_to_user(profile, email):
    """
    If the profile already has a linked User, update their email.
    If not, do nothing — credentials are generated separately by
    the admin-manager's generate_credentials flow.
    """
    if profile.user and email:
        profile.user.email = email
        profile.user.save(update_fields=['email'])


# ─────────────────────────────────────────────
# STUDENT
# ─────────────────────────────────────────────

@login_required(login_url='admin_login')
def edit_student(request, pk):
    qs = StudentProfile.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(school=school)
    student = get_object_or_404(qs, pk=pk)
    school = get_user_school(request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student, school=school)
        if form.is_valid():
            form.save()
            # Update email on linked user
            if student.user and form.cleaned_data.get('email'):
                student.user.email = form.cleaned_data['email']
                student.user.save(update_fields=['email'])
            messages.success(request, 'Student updated successfully.', extra_tags='students')
            return redirect('admin_console')
    else:
        # Pre-fill email from model field first, fallback to linked user
        initial_email = student.email or (student.user.email if student.user else '')
        form = StudentProfileForm(instance=student, initial={'email': initial_email}, school=get_user_school(request.user))
    return render(request, 'add_entry.html', {'form': form, 'model_name': 'Student', 'edit': True})


@login_required(login_url='admin_login')
def delete_student(request, pk):
    qs = StudentProfile.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(school=school)
    student = get_object_or_404(qs, pk=pk)
    return delete_model_entry(request, student, 'Student')


# ─────────────────────────────────────────────
# TEACHER
# ─────────────────────────────────────────────

@login_required(login_url='admin_login')
def add_teacher(request):
    school = get_user_school(request.user)
    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, school=school)
        if form.is_valid():
            teacher = form.save(commit=False)
            teacher.school = get_user_school(request.user)
            
            # Handle multiple document uploads
            import base64, json, uuid
            doc_files = request.FILES.getlist('doc_files[]')
            doc_titles = request.POST.getlist('doc_titles[]')
            if doc_files and doc_titles:
                docs = json.loads(teacher.documents_json or '[]')
                for i in range(len(doc_files)):
                    f = doc_files[i]
                    t = doc_titles[i] if i < len(doc_titles) else ''
                    if f and t:
                        docs.append({
                            'id': str(uuid.uuid4())[:8],
                            'title': t,
                            'file_name': f.name,
                            'file_content': base64.b64encode(f.read()).decode('utf-8'),
                            'file_type': f.content_type or 'application/octet-stream',
                            'uploaded_at': timezone.now().strftime('%d %b %Y')
                        })
                teacher.documents_json = json.dumps(docs)
            User = get_user_model()
            email = form.cleaned_data.get('email', '')
            # Generate username from full name
            base_username = form.cleaned_data['full_name'].replace(' ', '').lower()
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            import secrets
            user = User.objects.create_user(
                username=username,
                email=email,
                password=f"{username}123" 
            )
            user.role = 'teacher'
            user.save()

            teacher.user = user
            teacher.save()
            form.save_m2m()  # save ManyToMany fields like subjects

            messages.success(request, 'Teacher added successfully.', extra_tags='teachers')
            return redirect('/admin-console/?section=staff')
    else:
        form = TeacherProfileForm(school=school)
    return render(request, 'add_teacher.html', {'form': form, 'model_name': 'Teacher'})


@login_required(login_url='admin_login')
def edit_teacher(request, pk):
    from django.db.models import Q
    qs = TeacherProfile.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(Q(school=school) | Q(school__isnull=True))
    teacher = get_object_or_404(qs, pk=pk)
    school = get_user_school(request.user)

    # Check if user is an employee viewer (no salary access)
    hide_salary = False
    if getattr(request.user, 'role', None) == 'admin_manager':
        try:
            profile = request.user.admin_manager_profile
            hide_salary = profile.is_employee_viewer
        except Exception:
            pass

    salary_fields = ['salary', 'salary_type', 'working_days_per_week', 'bank_name', 'bank_account']
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        post_data = request.POST.copy()
        if hide_salary:
            for f in salary_fields:
                if f not in post_data or not post_data[f]:
                    post_data[f] = getattr(teacher, f, '') or ''
        form = TeacherProfileForm(post_data, request.FILES, instance=teacher, school=school)
        if form.is_valid():
            if hide_salary:
                for f in salary_fields:
                    if f in form.cleaned_data:
                        del form.cleaned_data[f]
            form.save()
            # Handle multiple document uploads
            import base64, json, uuid
            doc_files = request.FILES.getlist('doc_files[]')
            doc_titles = request.POST.getlist('doc_titles[]')
            if doc_files and doc_titles:
                docs = json.loads(teacher.documents_json or '[]')
                for i in range(len(doc_files)):
                    f = doc_files[i]
                    t = doc_titles[i] if i < len(doc_titles) else ''
                    if f and t:
                        docs.append({
                            'id': str(uuid.uuid4())[:8],
                            'title': t,
                            'file_name': f.name,
                            'file_content': base64.b64encode(f.read()).decode('utf-8'),
                            'file_type': f.content_type or 'application/octet-stream',
                            'uploaded_at': timezone.now().strftime('%d %b %Y')
                        })
                teacher.documents_json = json.dumps(docs)
                teacher.save(update_fields=['documents_json'])
            # Update email on the linked user
            if teacher.user and form.cleaned_data.get('email'):
                teacher.user.email = form.cleaned_data['email']
                teacher.user.save()
            messages.success(request, 'Teacher updated successfully.', extra_tags='teachers')
            if is_ajax:
                import json as _json
                return HttpResponse(_json.dumps({'ok': True, 'msg': 'Teacher updated successfully.'}), content_type='application/json')
            return redirect('/admin-console/?section=staff')
        elif is_ajax:
            import json as _json
            return HttpResponse(_json.dumps({'ok': False, 'errors': form.errors.as_json()}), content_type='application/json', status=400)
    else:
        form = TeacherProfileForm(
            instance=teacher,
            initial={'email': teacher.user.email if teacher.user else ''},
            school=get_user_school(request.user)
        )
        if hide_salary:
            for f in salary_fields:
                if f in form.fields:
                    del form.fields[f]
    import json
    documents = json.loads(teacher.documents_json or '[]')
    return render(request, 'add_teacher.html', {'form': form, 'model_name': 'Teacher', 'edit': True, 'teacher': teacher, 'documents': documents, 'hide_salary': hide_salary})


@login_required(login_url='admin_login')
def delete_teacher(request, pk):
    from django.db.models import Q
    qs = TeacherProfile.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(Q(school=school) | Q(school__isnull=True))
    teacher = get_object_or_404(qs, pk=pk)
    return delete_model_entry(request, teacher, 'Teacher')


# ─────────────────────────────────────────────
# STAFF DOCUMENTS
# ─────────────────────────────────────────────

import base64
import json
import uuid

def _get_docs(teacher):
    try:
        return json.loads(teacher.documents_json or '[]')
    except Exception:
        return []

def _save_docs(teacher, docs):
    teacher.documents_json = json.dumps(docs)
    teacher.save(update_fields=['documents_json'])

@login_required(login_url='admin_login')
def staff_documents(request, pk):
    teacher = get_object_or_404(TeacherProfile, pk=pk)
    documents = _get_docs(teacher)
    return render(request, 'staff_documents.html', {'teacher': teacher, 'documents': documents})

@login_required(login_url='admin_login')
def add_staff_document(request, pk):
    teacher = get_object_or_404(TeacherProfile, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.method == 'POST':
        titles = request.POST.getlist('titles[]')
        files = request.FILES.getlist('files[]')
        if not titles:
            titles = [request.POST.get('title', '')]
            files = [request.FILES.get('file')]
        docs = _get_docs(teacher)
        count = 0
        new_docs = []
        for title, f in zip(titles, files):
            title = (title or '').strip()
            if title and f:
                doc = {
                    'id': str(uuid.uuid4())[:8],
                    'title': title,
                    'file_name': f.name,
                    'file_content': base64.b64encode(f.read()).decode('utf-8'),
                    'file_type': f.content_type or 'application/octet-stream',
                    'uploaded_at': timezone.now().strftime('%d %b %Y')
                }
                docs.append(doc)
                new_docs.append(doc)
                count += 1
        if count:
            _save_docs(teacher, docs)
            if is_ajax:
                import json as _json
                safe_docs = [{k: v for k, v in d.items() if k != 'file_content'} for d in new_docs]
                return HttpResponse(_json.dumps({'ok': True, 'count': count, 'docs': safe_docs, 'total': len(docs)}), content_type='application/json')
            messages.success(request, f'{count} document(s) uploaded successfully.')
        else:
            if is_ajax:
                import json as _json
                return HttpResponse(_json.dumps({'ok': False, 'msg': 'Please provide both title and file.'}), content_type='application/json', status=400)
            messages.error(request, 'Please provide both title and file.')
    if is_ajax:
        import json as _json
        return HttpResponse(_json.dumps({'ok': False, 'msg': 'No file provided.'}), content_type='application/json', status=400)
    return redirect('staff_documents', pk=pk)

@login_required(login_url='admin_login')
def download_staff_document(request, pk, doc_id):
    teacher = get_object_or_404(TeacherProfile, pk=pk)
    docs = _get_docs(teacher)
    doc = next((d for d in docs if d['id'] == doc_id), None)
    if not doc:
        return HttpResponse('Document not found', status=404)
    file_bytes = base64.b64decode(doc['file_content'])
    response = HttpResponse(file_bytes, content_type=doc['file_type'])
    response['Content-Disposition'] = f'inline; filename="{doc["file_name"]}"'
    return response

@login_required(login_url='admin_login')
def delete_staff_document(request, pk, doc_id):
    teacher = get_object_or_404(TeacherProfile, pk=pk)
    docs = _get_docs(teacher)
    docs = [d for d in docs if d['id'] != doc_id]
    _save_docs(teacher, docs)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    messages.success(request, 'Document deleted successfully.')
    return redirect('staff_documents', pk=pk)


# ─────────────────────────────────────────────
# PARENT
# ─────────────────────────────────────────────

@login_required(login_url='admin_login')
def add_student(request):
    school = get_user_school(request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, school=school)
        if form.is_valid():
            student = form.save(commit=False)
            student.school = get_user_school(request.user)
            email = form.cleaned_data.get('email', '')
            
            User = get_user_model()
            base_username = form.cleaned_data['full_name'].replace(' ', '').lower()
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                password=f"{username}123"
            )
            user.role = 'student'
            user.save()

            student.user = user
            student.save()
            form.save_m2m()

            messages.success(request, 'Student added successfully.', extra_tags='students')
            return redirect('admin_console')
    else:
        form = StudentProfileForm(school=school)
    return render(request, 'add_entry.html', {'form': form, 'model_name': 'Student'})


@login_required(login_url='admin_login')
def add_parent(request):
    school = get_user_school(request.user)
    if request.method == 'POST':
        form = ParentProfileForm(request.POST, request.FILES, school=school)
        if form.is_valid():
            parent = form.save(commit=False)
            parent.school = get_user_school(request.user)
            email = form.cleaned_data.get('email', '')

            User = get_user_model()

            base_username = form.cleaned_data['full_name'].replace(' ', '').lower()
            username = base_username
            counter = 1

            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            password = f"{username}123"

            # ✅ Create User account (this will appear in admin)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            # ✅ Assign role
            user.role = 'parent'
            user.save()

            # ✅ Link profile to user
            parent.user = user
            parent.save()
            form.save_m2m() 

            messages.success(request, 'Parent added successfully.', extra_tags='parents')

            return redirect('admin_console')

    else:
        form = ParentProfileForm(school=school)

    return render(request, 'add_entry.html', {'form': form, 'model_name': 'Parent'})



@login_required(login_url='admin_login')
def edit_parent(request, pk):
    qs = ParentProfile.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(school=school)
    parent = get_object_or_404(qs, pk=pk)
    school = get_user_school(request.user)
    if request.method == 'POST':
        form = ParentProfileForm(request.POST, request.FILES, instance=parent, school=school)
        if form.is_valid():
            form.save()
            # Update email on linked user
            if parent.user and form.cleaned_data.get('email'):
                parent.user.email = form.cleaned_data['email']
                parent.user.save(update_fields=['email'])
            messages.success(request, 'Parent updated successfully.', extra_tags='parents')
            return redirect('admin_console')
    else:
        # Pre-fill email from model field first, fallback to linked user
        initial_email = parent.email or (parent.user.email if parent.user else '')
        form = ParentProfileForm(instance=parent, initial={'email': initial_email}, school=get_user_school(request.user))
    return render(request, 'add_entry.html', {'form': form, 'model_name': 'Parent', 'edit': True})

@login_required(login_url='admin_login')
def delete_parent(request, pk):
    qs = ParentProfile.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(school=school)
    parent = get_object_or_404(qs, pk=pk)
    return delete_model_entry(request, parent, 'Parent')


from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

def parent_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                parent = ParentProfile.objects.get(user=user)  # now works after migration
                login(request, user)
                return redirect('parent_dashboard')
            except ParentProfile.DoesNotExist:
                messages.error(request, 'No parent profile linked to this account.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'parent_login.html')

@login_required
def parent_dashboard(request):
    parent = get_object_or_404(ParentProfile, user=request.user)
    students = list(parent.students.all().select_related('student_class'))

    # Attach attendance summary directly onto each student object
    for student in students:
        records = Attendance.objects.filter(student=student)
        present = records.filter(status='present').count()
        absent  = records.filter(status='absent').count()
        leave   = records.filter(status='leave').count()
        total   = present + absent + leave
        student.att_present    = present
        student.att_absent     = absent
        student.att_leave      = leave
        student.att_total      = total
        student.att_percentage = round((present / total) * 100) if total else 0

        # Attach timetable directly onto student
        DAY_ORDER = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
        slots = TimetableSlot.objects.filter(
            assigned_class=student.student_class
        ).select_related('subject','teacher').order_by('day','period_number')
        timetable = {}
        for slot in slots:
            timetable.setdefault(slot.day, []).append(slot)
        student.timetable = {
            day: timetable[day]
            for day in DAY_ORDER
            if day in timetable
        }

    all_pcts = [s.att_percentage for s in students]
    overall_attendance_pct = round(sum(all_pcts) / len(all_pcts)) if all_pcts else 0

    child_class_ids = [s.student_class_id for s in students]
    all_tasks        = HomeTask.objects.filter(assigned_class__in=child_class_ids).select_related('assigned_class','subject').order_by('-assigned_date')
    recent_tasks     = all_tasks[:10]
    total_pending_tasks = all_tasks.filter(due_date__gte=timezone.now().date()).count()

    all_results    = Result.objects.filter(student__in=students).select_related('student','exam','exam__subject','student__student_class').order_by('-exam__exam_date')
    recent_results = all_results[:10]
    total_exams    = all_results.values('exam').distinct().count()

    DAY_ORDER = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']

    context = {
        'parent':                 parent,
        'students':               students,
        'overall_attendance_pct': overall_attendance_pct,
        'all_tasks':              all_tasks,
        'recent_tasks':           recent_tasks,
        'total_pending_tasks':    total_pending_tasks,
        'all_results':            all_results,
        'recent_results':         recent_results,
        'total_exams':            total_exams,
        'all_subjects':           Subject.objects.all(),
        'timetable_days':         DAY_ORDER,
    }
    return render(request, 'parent_dashboard.html', context)


# ─────────────────────────────────────────────
# CLASS
# ─────────────────────────────────────────────

@login_required(login_url='admin_login')
def add_class(request):
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            cls = form.save(commit=False)
            cls.school = get_user_school(request.user)
            cls.save()
            messages.success(request, 'Class added successfully.', extra_tags='classes')
            return redirect('admin_console')
    else:
        form = ClassForm()
    return render(request, 'add_entry.html', {'form': form, 'model_name': 'Class'})

@login_required(login_url='admin_login')
def edit_class(request, pk):
    qs = Class.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(school=school)
    cls = get_object_or_404(qs, pk=pk)
    return edit_model_entry(request, cls, ClassForm, 'Class', 'add_entry.html')

@login_required(login_url='admin_login')
def delete_class(request, pk):
    qs = Class.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(school=school)
    cls = get_object_or_404(qs, pk=pk)
    return delete_model_entry(request, cls, 'Class')


# ─────────────────────────────────────────────
# SUBJECT
# ─────────────────────────────────────────────

@login_required(login_url='admin_login')
def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.school = get_user_school(request.user)
            subject.save()
            messages.success(request, 'Subject added successfully.', extra_tags='subjects')
            return redirect('admin_console')
    else:
        form = SubjectForm()
    return render(request, 'add_entry.html', {'form': form, 'model_name': 'Subject'})

@login_required(login_url='admin_login')
def edit_subject(request, pk):
    qs = Subject.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(school=school)
    subject = get_object_or_404(qs, pk=pk)
    return edit_model_entry(request, subject, SubjectForm, 'Subject', 'add_entry.html')

@login_required(login_url='admin_login')
def delete_subject(request, pk):
    qs = Subject.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(school=school)
    subject = get_object_or_404(qs, pk=pk)
    return delete_model_entry(request, subject, 'Subject')


# ─────────────────────────────────────────────
# ASSIGNMENT
# ─────────────────────────────────────────────

@login_required(login_url='admin_login')
def add_assignment(request):
    if request.method == 'POST':
        form = TeacherSubjectAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment added successfully.', extra_tags='assignments')
            return redirect('admin_console')
    else:
        qs = Class.objects.all()
        school = get_user_school(request.user)
        if not request.user.is_superuser and school:
            qs = qs.filter(school=school)
        form = TeacherSubjectAssignmentForm()
        form.fields['assigned_class'].queryset = qs
        if not request.user.is_superuser and school:
            form.fields['teacher'].queryset = TeacherProfile.objects.filter(school=school)
            form.fields['subject'].queryset = Subject.objects.filter(school=school)
    return render(request, 'add_entry.html', {'form': form, 'model_name': 'Teacher Assignment'})

@login_required(login_url='admin_login')
def edit_assignment(request, pk):
    qs = TeacherSubjectAssignment.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(assigned_class__school=school)
    assignment = get_object_or_404(qs, pk=pk)
    return edit_model_entry(request, assignment, TeacherSubjectAssignmentForm, 'Teacher Assignment', 'add_entry.html')

@login_required(login_url='admin_login')
def delete_assignment(request, pk):
    qs = TeacherSubjectAssignment.objects.all()
    school = get_user_school(request.user)
    if not request.user.is_superuser and school:
        qs = qs.filter(assigned_class__school=school)
    assignment = get_object_or_404(qs, pk=pk)
    return delete_model_entry(request, assignment, 'Assignment')


# ─────────────────────────────────────────────
# UTILITY
# ─────────────────────────────────────────────

def subjects_by_class(request, class_id):
    """Returns subjects assigned to a given class via TeacherSubjectAssignment."""
    subjects = Subject.objects.filter(
        assignments__assigned_class_id=class_id
    ).distinct().values('id', 'name', 'code')
    return JsonResponse({'subjects': list(subjects)})

# ─────────────────────────────────────────────
# TEACHER DASHBOARD
# ─────────────────────────────────────────────
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def get_teacher(request):
    if not request.user.is_authenticated:
        return None
    
    from .models import TeacherProfile
    
    # 1. Try to find the profile directly linked to this user
    teacher = TeacherProfile.objects.filter(user=request.user).first()
    if teacher:
        return teacher

    # 2. Safety check for Admins (Superusers)
    # If you are logged in as an admin but haven't linked 'arooba' to a profile yet,
    # this will let you see the dashboard using the first teacher profile available.
    if request.user.is_superuser:
        return TeacherProfile.objects.first()

    return None
    
from django.shortcuts import redirect

@login_required(login_url='teacher_login')

def teacher_dashboard(request):
    # --- DEBUG SECTION ---
    print(f"DEBUG: User is -> {request.user}")
    print(f"DEBUG: Is authenticated? -> {request.user.is_authenticated}")
    # ---------------------

    teacher = get_teacher(request)
    if not teacher:
        from django.contrib.auth import logout
        logout(request)
        return redirect('teacher_login')

    today = timezone.now().date()

    # ── YOUR EXISTING DASHBOARD LOGIC ──
    assignment_qs = TeacherSubjectAssignment.objects.filter(
        teacher=teacher
    ).select_related('assigned_class', 'subject')
    assigned_class_ids = assignment_qs.values_list('assigned_class_id', flat=True).distinct()
    assigned_classes = Class.objects.filter(id__in=assigned_class_ids)

    for cls in assigned_classes:
        cls_students = StudentProfile.objects.filter(student_class=cls)
        cls.total_students = cls_students.count()
        today_att = Attendance.objects.filter(student__in=cls_students, date=today, marked_by=teacher)
        cls.present_today = today_att.filter(status='present').count()
        cls.absent_today  = today_att.filter(status='absent').count()
        cls.leave_today   = today_att.filter(status='leave').count()

    students = StudentProfile.objects.filter(student_class__in=assigned_classes).order_by('roll_number')
    my_subjects = Subject.objects.filter(assignments__teacher=teacher).distinct()
    my_hometasks = HomeTask.objects.filter(assigned_by=teacher).select_related('assigned_class', 'subject')
    my_exams = Exam.objects.filter(created_by=teacher).select_related('subject', 'assigned_class')
    my_uploaded_results = Result.objects.filter(uploaded_by=teacher).select_related('student', 'exam')
    my_attendance_records = Attendance.objects.filter(marked_by=teacher).select_related('student__student_class', 'subject')[:200]
    results = Result.objects.filter(exam__in=my_exams).select_related('student', 'exam')

    all_att_today = Attendance.objects.filter(student__in=students, date=today, marked_by=teacher)
    present_today = all_att_today.filter(status='present').count()
    absent_today  = all_att_today.filter(status='absent').count()
    leave_today   = all_att_today.filter(status='leave').count()

    my_class = Class.objects.filter(class_teacher=teacher).first()

    DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slots = TimetableSlot.objects.filter(teacher=teacher).select_related('subject', 'assigned_class').order_by('day', 'period_number')

    teacher_timetable = {}
    for slot in slots:
        teacher_timetable.setdefault(slot.day, []).append(slot)

    teacher_timetable = {
        day: teacher_timetable[day]
        for day in DAY_ORDER
        if day in teacher_timetable
    }

    context = {
        'teacher': teacher,
        'assigned_classes': assigned_classes,
        'students': students,
        'my_subjects': my_subjects,
        'my_hometasks': my_hometasks,
        'my_exams': my_exams,
        'my_uploaded_results': my_uploaded_results,
        'my_attendance_records': my_attendance_records,
        'results': results,
        'present_today': present_today,
        'absent_today': absent_today,
        'leave_today': leave_today,
        'total_students': students.count(),
        'today': today,
        'teacher_timetable': teacher_timetable,
        'timetable_days': list(teacher_timetable.keys()),
        'upcoming_lectures': slots,
        'my_class': my_class,
    }

    return render(request, 'teacher_dashboard.html', context)

def teacher_mark_attendance(request):
    teacher = get_teacher(request)
    if request.method == 'POST':
        class_id   = request.POST.get('class_id')
        date_str   = request.POST.get('date_field') or request.POST.get('date')
        subject_id = request.POST.get('subject_field') or request.POST.get('subject')

        # ✅ Validate required fields
        if not class_id or not subject_id:
            messages.error(request, 'Please select a class and subject before saving.', extra_tags='attendance')
            return redirect('/teacher_dashboard/?tab=attendance')

        cls      = get_object_or_404(Class, id=class_id)
        subject  = get_object_or_404(Subject, id=subject_id)
        students = StudentProfile.objects.filter(student_class=cls)

        for student in students:
            status = request.POST.get(f'status_{student.id}', 'present')
            Attendance.objects.update_or_create(
                student=student,
                subject=subject,
                date=date_str,
                defaults={
                    'student_class': cls,
                    'marked_by': teacher,
                    'status': status,
                }
            )
        messages.success(request, f'Attendance saved for {cls} ({students.count()} students).', extra_tags='attendance')
        return redirect('/teacher_dashboard/?tab=attendance')

    return redirect('teacher_dashboard')

def teacher_add_hometask(request):
    teacher = get_teacher(request)
    if request.method == 'POST':
        cls     = get_object_or_404(Class, id=request.POST.get('class_id'))
        subject = get_object_or_404(Subject, id=request.POST.get('subject'))
        HomeTask.objects.create(
            title         = request.POST.get('title'),
            description   = request.POST.get('description', ''),
            assigned_class= cls,
            subject       = subject,
            assigned_by   = teacher,
            assigned_date = request.POST.get('assigned_date'),
            due_date      = request.POST.get('due_date'),
            attachment    = request.FILES.get('attachment'),
        )
        messages.success(request, 'Task uploaded successfully.', extra_tags='hometasks')
        return redirect('teacher_dashboard')
    return redirect('teacher_dashboard')


def teacher_edit_hometask(request, pk):
    teacher = get_teacher(request)
    task = get_object_or_404(HomeTask, id=pk, assigned_by=teacher)
    if request.method == 'POST':
        task.title       = request.POST.get('title', task.title)
        task.description = request.POST.get('description', task.description)
        task.due_date    = request.POST.get('due_date', task.due_date)
        if request.FILES.get('attachment'):
            task.attachment = request.FILES['attachment']
        task.save()
        messages.success(request, 'Task updated.', extra_tags='hometasks')
        return redirect('teacher_dashboard')
    return render(request, 'teacher_edit_hometask.html', {'task': task})


def teacher_delete_hometask(request, pk):
    teacher = get_teacher(request)
    task = get_object_or_404(HomeTask, id=pk, assigned_by=teacher)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted.', extra_tags='hometasks')
    return redirect('teacher_dashboard')


def teacher_add_exam(request):
    teacher = get_teacher(request)
    if request.method == 'POST':
        Exam.objects.create(
            name              = request.POST['name'],
            subject_id        = request.POST['subject'],
            assigned_class_id = request.POST['assigned_class'],
            created_by        = teacher,
            exam_date         = request.POST['exam_date'],
            total_marks       = request.POST.get('total_marks', 100),
            passing_marks     = request.POST.get('passing_marks', 40),
        )
        messages.success(request, 'Exam created.', extra_tags='exams')
        return redirect('/teacher_dashboard/?tab=exams-marks')

        return redirect('teacher_dashboard')


def teacher_edit_exam(request, pk):
    teacher = get_teacher(request)
    exam = get_object_or_404(Exam, id=pk, created_by=teacher)
    if request.method == 'POST':
        exam.name          = request.POST.get('name', exam.name)
        exam.exam_date     = request.POST.get('exam_date', exam.exam_date)
        exam.total_marks   = request.POST.get('total_marks', exam.total_marks)
        exam.passing_marks = request.POST.get('passing_marks', exam.passing_marks)
        exam.save()
        messages.success(request, 'Exam updated.', extra_tags='exams')
        return redirect('teacher_dashboard')
    return render(request, 'teacher_edit_exam.html', {'exam': exam})


def teacher_delete_exam(request, pk):
    teacher = get_teacher(request)
    exam = get_object_or_404(Exam, id=pk, created_by=teacher)
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted.', extra_tags='exams')
    return redirect('teacher_dashboard')


def teacher_add_result(request):
    teacher = get_teacher(request)
    if request.method == 'POST':
        exam_id = request.POST.get('exam')
        if not exam_id:
            messages.error(request, 'Please select an exam.', extra_tags='results')
            return redirect('teacher_dashboard')

        exam = get_object_or_404(Exam, id=exam_id)
        students = StudentProfile.objects.filter(student_class=exam.assigned_class)

        saved_count = 0
        for student in students:
            marks_value = request.POST.get(f'marks_{student.id}', '').strip()
            if marks_value == '':
                continue  # skip students with no marks entered
            try:
                marks = float(marks_value)
            except ValueError:
                continue
            Result.objects.update_or_create(
                student=student,
                exam=exam,
                defaults={
                    'marks_obtained': marks,
                    'uploaded_by': teacher,
                }
            )
            saved_count += 1

        messages.success(request, f'Marks saved for {saved_count} student(s).', extra_tags='results')
        return redirect('/teacher_dashboard/?tab=exams-marks')

    return redirect('teacher_dashboard')

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required



import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required


# ─────────────────────────────────────────────
# TIMETABLE — SAVE
# ─────────────────────────────────────────────

@login_required(login_url='admin_login')
@require_POST
def save_timetable(request):
    """
    POST /timetable/save/
    Body:
    {
        "class_id": 3,
        "slots": [
            {
                "day":           "Monday",
                "period_number": 1,
                "start_time":    "08:00",
                "end_time":      "08:45",
                "duration":      45,
                "subject_name":  "Mathematics",
                "teacher_name":  "Mr. Ali"      // empty string = no teacher
            },
            ...
        ]
    }
    Full-replace strategy: deletes ALL existing slots for the class, then inserts fresh ones.
    The JS sends ALL days at once on "Save Timetable".
    """
    try:
        data     = json.loads(request.body)
        class_id = data.get('class_id')
        slots    = data.get('slots', [])

        if not class_id:
            return JsonResponse({'status': 'error', 'message': 'class_id missing'}, status=400)

        # Validate class exists
        klass = get_object_or_404(Class, pk=class_id)

        # Full replace for this class
        TimetableSlot.objects.filter(assigned_class=klass).delete()

        created = 0
        skipped = 0
        for s in slots:
            subject_name = s.get('subject_name', '').strip()
            teacher_name = s.get('teacher_name', '').strip()

            if not subject_name:
                skipped += 1
                continue  # empty row — skip

            subject = Subject.objects.filter(name=subject_name).first()
            if not subject:
                skipped += 1
                continue  # subject not found — skip silently

            teacher = None
            if teacher_name:
                teacher = TeacherProfile.objects.filter(full_name=teacher_name).first()

            TimetableSlot.objects.create(
                assigned_class=klass,
                subject=subject,
                teacher=teacher,
                day=s.get('day'),
                period_number=s.get('period_number'),
                start_time=s.get('start_time'),
                end_time=s.get('end_time'),
                duration=s.get('duration', 45),
            )
            created += 1

        return JsonResponse({
            'status':  'ok',
            'created': created,
            'skipped': skipped,
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ─────────────────────────────────────────────
# TIMETABLE — LOAD
# ─────────────────────────────────────────────

@login_required(login_url='admin_login')
@require_GET
def load_timetable(request):
    """
    GET /timetable/load/?class_id=3
    Returns all saved slots for the given class, grouped by day.
    Response:
    {
        "status": "ok",
        "class_id": 3,
        "slots": [
            {
                "day":           "Monday",
                "period_number": 1,
                "start_time":    "08:00",
                "end_time":      "08:45",
                "duration":      45,
                "subject_name":  "Mathematics",
                "teacher_name":  "Mr. Ali"
            },
            ...
        ]
    }
    """
    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'status': 'error', 'message': 'class_id is required'}, status=400)

    slots = TimetableSlot.objects.filter(
        assigned_class_id=class_id
    ).select_related('subject', 'teacher').order_by('day', 'period_number')

    payload = []
    for s in slots:
        payload.append({
            'day':           s.day,
            'period_number': s.period_number,
            'start_time':    s.start_time.strftime('%H:%M'),
            'end_time':      s.end_time.strftime('%H:%M'),
            'duration':      s.duration,
            'subject_name':  s.subject.name,
            'teacher_name':  s.teacher.full_name if s.teacher else '',
        })

    return JsonResponse({'status': 'ok', 'class_id': int(class_id), 'slots': payload})


# ─────────────────────────────────────────────
# TIMETABLE — CLEAR
# ─────────────────────────────────────────────

@login_required(login_url='admin_login')
@require_POST
def clear_timetable(request):
    """
    POST /timetable/clear/
    Body: { "class_id": 3 }   → clears all slots for that class
          {}                   → clears ALL slots (admin only)
    """
    try:
        data     = json.loads(request.body)
        class_id = data.get('class_id')

        qs = TimetableSlot.objects.all()
        if class_id:
            qs = qs.filter(assigned_class_id=class_id)

        deleted, _ = qs.delete()
        return JsonResponse({'status': 'ok', 'deleted': deleted})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)



from django.contrib.auth import authenticate, login, logout

from django.contrib.auth import logout, authenticate, login


def teacher_login(request):
    context = {}

    msg = request.GET.get("msg")
    if msg == "reset_sent":
        context['success_msg'] = "Reset link sent to your email."
    if msg == "reset_done":
        context['success_msg'] = "Password changed successfully. You can now log in."

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if getattr(user, 'role', None) == 'teacher' or hasattr(user, 'teacher_profile'):
                login(request, user)
                return redirect('teacher_dashboard')
            else:
                context['error_msg'] = 'This account is not registered as a teacher.'
        else:
            context['error_msg'] = 'Invalid username or password.'

    return render(request, 'teacher_login.html', context)

def teacher_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        User = get_user_model()
        users = User.objects.filter(email=email, role='teacher')

        for user in users:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(
                f'/accounts/teacher/reset/{uid}/{token}/'
            )
            send_mail(
                subject='Teacher Password Reset',
                message=f'Click the link to reset your password: {reset_link}',
                from_email='nafiaaziz.500@gmail.com',
                recipient_list=[email],
            )

        return redirect('/teacher/login/?msg=reset_sent')

    return render(request, 'password_reset.html')
from django.contrib.auth import logout
@require_POST
def teacher_logout(request):
    logout(request)
    return redirect('teacher_login')

# ─────────────────────────────────────────────
# STUDENT PORTAL — Views
# Add these to your views.py
# ─────────────────────────────────────────────

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone


def get_student(request):
    """Return the StudentProfile linked to the logged-in user, or None."""
    if not request.user.is_authenticated:
        return None
    return StudentProfile.objects.filter(user=request.user).first()


# ─── LOGIN ───────────────────────────────────

def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Accept only users whose StudentProfile exists
            if StudentProfile.objects.filter(user=user).exists():
                login(request, user)
                return redirect('student_dashboard')
            else:
                messages.error(request, 'This account is not registered as a student.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'student_login.html')


# ─── LOGOUT ──────────────────────────────────

from django.views.decorators.http import require_POST as _require_POST

@_require_POST
def student_logout(request):
    logout(request)
    return redirect('/')


# ─── DASHBOARD ───────────────────────────────

def student_dashboard(request):
    student = get_student(request)
    if not student:
        logout(request)
        return redirect('/')

    today      = timezone.now().date()
    today_name = today.strftime('%A')          # e.g. "Monday"

    # ── Timetable for this student's class ──
    DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    all_slots = TimetableSlot.objects.filter(
        assigned_class=student.student_class
    ).select_related('subject', 'teacher').order_by('day', 'period_number')

    student_timetable = {}
    for slot in all_slots:
        student_timetable.setdefault(slot.day, []).append(slot)

    # Keep days in order
    student_timetable = {
        day: student_timetable[day]
        for day in DAY_ORDER
        if day in student_timetable
    }

    # Today's slots for the overview card
    today_slots = student_timetable.get(today_name, [])

    # ── Attendance ──
    attendance_records = Attendance.objects.filter(
        student=student
    ).select_related('subject', 'marked_by').order_by('-date')

    present_count = attendance_records.filter(status='present').count()
    absent_count  = attendance_records.filter(status='absent').count()
    leave_count   = attendance_records.filter(status='leave').count()
    total_att     = present_count + absent_count + leave_count
    attendance_pct = round((present_count / total_att * 100)) if total_att > 0 else 0

    # ── Home Tasks for this student's class ──
    hometasks = HomeTask.objects.filter(
        assigned_class=student.student_class
    ).select_related('subject', 'assigned_by').order_by('due_date')

    recent_tasks = hometasks[:5]

    context = {
        'student':           student,
        # timetable
        'student_timetable': student_timetable,
        'timetable_days':    list(student_timetable.keys()),
        'today_slots':       today_slots,
        'timetable_periods': all_slots.count(),
        # attendance
        'attendance_records': attendance_records,
        'present_count':     present_count,
        'absent_count':      absent_count,
        'leave_count':       leave_count,
        'attendance_pct':    attendance_pct,
        # tasks
        'hometasks':         hometasks,
        'recent_tasks':      recent_tasks,
        'total_tasks':       hometasks.count(),
        # misc
        'today':             today,
    }
    return render(request, 'student_dashboard.html', context)



def credentials_page(request):
    role = request.GET.get("role")
    school = get_user_school(request.user)
    school_filter = {}
    if not request.user.is_superuser and school:
        school_filter = {'school': school}

    users = []
    if role == "students":
        users = StudentProfile.objects.filter(**school_filter)
    elif role == "teachers":
        users = TeacherProfile.objects.filter(**school_filter)
    elif role == "parents":
        users = ParentProfile.objects.filter(**school_filter)

    return render(request, "credentials.html", {
        "users": users,
        "role": role
    })

from accounts.models import User
from django.shortcuts import redirect
from django.contrib import messages


from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import User
from academics.models import StudentProfile, TeacherProfile, ParentProfile

def generate_selected_credentials(request):
    if request.method == "POST":
        ids = request.POST.getlist("users")
        credentials = []
        school = get_user_school(request.user)

        for uid in ids:
            school_filter = {}
            if not request.user.is_superuser and school:
                school_filter = {'school': school}
            student = StudentProfile.objects.filter(id=uid, **school_filter).first()

            if student and not student.user:
                username = student.full_name.replace(" ", "").lower()
                password = f"{username}123"

                user = User.objects.create_user(
                    username=username,
                    password=password
                )

                student.user = user
                student.save()

                credentials.append({
                    "name": student.full_name,
                    "username": username,
                    "password": password
                })

        role = request.GET.get("role", "students")
        users = StudentProfile.objects.all() if role == "students" else []

        return render(request, "credentials.html", {
            "users": users,
            "role": role,
            "credentials": credentials
        })
    
    # If GET request, redirect to credentials page instead of returning None
    return redirect("credentials_page")


# ─────────────────────────────────────────────
# CREDENTIALS — replace ALL existing generate_credentials functions
# with this single one at the BOTTOM of views.py
# Also remove: credentials_page, generate_selected_credentials
# ─────────────────────────────────────────────

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group

# Use YOUR custom User model — not django.contrib.auth.models.User
from accounts.models import User  


@csrf_exempt
def generate_credentials(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        credentials = data.get('credentials', [])
        school = get_user_school(request.user)
        results = []

        for c in credentials:
            username  = c['username']
            password = f"{username}123" 
            user_type = c['type']
            user_id   = c['id']

            school_filter = {}
            if not request.user.is_superuser and school:
                school_filter = {'school': school}

            user, created = User.objects.get_or_create(username=username)
            user.set_password(password)
            user.save()

            group_name = user_type.capitalize()
            group, _   = Group.objects.get_or_create(name=group_name)
            user.groups.set([group])

            if user_type == 'student':
                from academics.models import StudentProfile
                StudentProfile.objects.filter(pk=user_id, **school_filter).update(user=user)

            elif user_type == 'teacher':
                from academics.models import TeacherProfile
                TeacherProfile.objects.filter(pk=user_id, **school_filter).update(user=user)

            elif user_type == 'parent':
                from academics.models import ParentProfile
                ParentProfile.objects.filter(pk=user_id, **school_filter).update(user=user)

            results.append({
                'username': username,
                'type':     user_type,
                'created':  created,
            })

        return JsonResponse({'status': 'ok', 'count': len(results), 'results': results})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
def parent_logout(request):
    logout(request)
    return redirect('/')


# ─────────────────────────────────────────────
# DATA IMPORT / EXPORT
# ─────────────────────────────────────────────

from django.http import HttpResponse
from .data_handlers import (
    export_to_csv, export_to_excel,
    IMPORTERS, EXPORTERS,
)

ALLOWED_EXPORT_TYPES = list(EXPORTERS.keys())
ALLOWED_IMPORT_TYPES = list(IMPORTERS.keys())


@login_required(login_url='admin_login')
def export_data(request):
    role = getattr(request.user, 'role', None)
    if not (request.user.is_authenticated and role in ('admin', 'admin_manager', 'principal')):
        return HttpResponse('Unauthorized', status=403)

    data_type = request.GET.get('type', '')
    fmt = request.GET.get('format', 'csv')

    if data_type not in ALLOWED_EXPORT_TYPES:
        messages.error(request, f'Invalid export type: {data_type}', extra_tags='import-export')
        return redirect('admin_console')

    school = get_user_school(request.user)

    if fmt == 'xlsx':
        content = export_to_excel(data_type, school)
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ext = 'xlsx'
    else:
        content = export_to_csv(data_type, school)
        content_type = 'text/csv'
        ext = 'csv'

    response = HttpResponse(content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{data_type}_export.{ext}"'
    return response


@login_required(login_url='admin_login')
def import_data(request):
    role = getattr(request.user, 'role', None)
    if not (request.user.is_authenticated and role in ('admin', 'admin_manager', 'principal')):
        return HttpResponse('Unauthorized', status=403)

    if request.method != 'POST':
        return redirect('admin_console')

    data_type = request.POST.get('type', '')
    uploaded_file = request.FILES.get('file')

    if data_type not in ALLOWED_IMPORT_TYPES:
        messages.error(request, f'Invalid import type: {data_type}', extra_tags='import-export')
        return redirect('admin_console')

    if not uploaded_file:
        messages.error(request, 'Please select a file to import.', extra_tags='import-export')
        return redirect('admin_console')

    school = get_user_school(request.user)
    handler = IMPORTERS[data_type]
    result = handler(uploaded_file, school)

    if result['errors']:
        error_preview = result['errors'][:5]
        error_msg = f"Imported {result['success']} record(s). {len(result['errors'])} error(s): " + '; '.join(error_preview)
        messages.warning(request, error_msg, extra_tags='import-export')
    else:
        messages.success(request, f'Successfully imported {result["success"]} {data_type} record(s).', extra_tags='import-export')

    return redirect('admin_console')
