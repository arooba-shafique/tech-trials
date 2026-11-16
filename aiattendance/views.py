import json
import mimetypes

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from academics.models import Class, StudentProfile, Subject, TeacherSubjectAssignment
from academics.views import get_teacher

from .models import FaceEmbedding
from .services import (
    ALLOWED_STATUSES,
    DEFAULT_MODEL_VERSION,
    normalize_embedding,
    parse_iso_date,
    save_attendance_statuses,
    trim_embeddings,
)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _json_error(message, status=400):
    return JsonResponse({'ok': False, 'error': str(message)}, status=status)


def _parse_json_body(request):
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _require_teacher(request):
    """Return the TeacherProfile for this request or a JSON 403 response."""
    if not request.user.is_authenticated:
        return None, _json_error('Not authenticated', 403)
    teacher = get_teacher(request)
    if not teacher:
        return None, _json_error('No teacher profile for this account', 403)
    return teacher, None


def _assigned_classes(teacher):
    assignment_ids = TeacherSubjectAssignment.objects.filter(
        teacher=teacher
    ).values_list('assigned_class_id', flat=True)
    class_teacher_ids = Class.objects.filter(class_teacher=teacher).values_list('id', flat=True)
    return Class.objects.filter(id__in=set(assignment_ids) | set(class_teacher_ids)).order_by('name', 'section')


def _can_access_class(user, teacher, cls):
    if user.is_superuser:
        return True
    if cls.class_teacher_id == teacher.id:
        return True
    return cls.id in set(
        TeacherSubjectAssignment.objects.filter(teacher=teacher)
        .values_list('assigned_class_id', flat=True)
    )


def _class_subjects(cls):
    return list(
        Subject.objects.filter(assignments__assigned_class_id=cls.id)
        .distinct()
        .order_by('name')
        .values('id', 'name', 'code')
    )


def _photo_url(student):
    if student.profile_picture:
        return f'/api/ai/photo/{student.id}/'
    return ''


def _class_list_with_counts(teacher):
    classes = _assigned_classes(teacher)
    for cls in classes:
        students = StudentProfile.objects.filter(student_class=cls)
        cls.total_students = students.count()
        cls.enrolled_students = (
            FaceEmbedding.objects.filter(student__in=students)
            .values('student_id').distinct().count()
        )
    return classes


# ─────────────────────────────────────────────
# Pages
# ─────────────────────────────────────────────

@login_required(login_url='teacher_login')
def ai_session_page(request):
    """Live AI attendance session page (camera → review → save)."""
    teacher = get_teacher(request)
    if not teacher:
        logout(request)
        return redirect('teacher_login')

    context = {
        'teacher': teacher,
        'assigned_classes': _class_list_with_counts(teacher),
        'today': timezone.now().date(),
    }
    return render(request, 'aiattendance/ai_session.html', context)


@login_required(login_url='teacher_login')
def ai_enroll_page(request):
    """Face enrollment page: auto from profile photos + live camera capture."""
    teacher = get_teacher(request)
    if not teacher:
        logout(request)
        return redirect('teacher_login')

    context = {
        'teacher': teacher,
        'assigned_classes': _class_list_with_counts(teacher),
    }
    return render(request, 'aiattendance/enroll.html', context)


# ─────────────────────────────────────────────
# API: roster / embeddings / photo
# ─────────────────────────────────────────────

@require_GET
def api_class_roster(request, class_id):
    """Students of a class with enrollment status + subjects offered."""
    teacher, err = _require_teacher(request)
    if err:
        return err
    cls = get_object_or_404(Class, id=class_id)
    if not _can_access_class(request.user, teacher, cls):
        return _json_error('You do not have access to this class', 403)

    students = StudentProfile.objects.filter(student_class=cls).order_by('roll_number', 'full_name')
    enrolled = dict(
        FaceEmbedding.objects.filter(student__in=students)
        .values('student_id')
        .annotate(n=Count('id'))
        .values_list('student_id', 'n')
    )

    roster = [
        {
            'id': s.id,
            'name': s.full_name,
            'roll': s.roll_number or '',
            'photo': _photo_url(s),
            'enrolled': enrolled.get(s.id, 0),
        }
        for s in students
    ]

    return JsonResponse({
        'ok': True,
        'class': {'id': cls.id, 'name': str(cls)},
        'students': roster,
        'subjects': _class_subjects(cls),
    })


@require_GET
def api_class_embeddings(request, class_id):
    """All enrolled face embeddings for a class roster (for in-browser matching)."""
    teacher, err = _require_teacher(request)
    if err:
        return err
    cls = get_object_or_404(Class, id=class_id)
    if not _can_access_class(request.user, teacher, cls):
        return _json_error('You do not have access to this class', 403)

    students = StudentProfile.objects.filter(student_class=cls)
    rows = (
        FaceEmbedding.objects.filter(student__in=students)
        .order_by('student_id', '-created_at')
        .values('student_id', 'embedding', 'model_version')
    )

    grouped = []
    index = {}
    for row in rows:
        sid = row['student_id']
        if sid not in index:
            index[sid] = {'id': sid, 'vectors': [], 'model_versions': []}
            grouped.append(index[sid])
        index[sid]['vectors'].append(row['embedding'])
        index[sid]['model_versions'].append(row['model_version'])

    return JsonResponse({
        'ok': True,
        'class': {'id': cls.id, 'name': str(cls)},
        'model_version': DEFAULT_MODEL_VERSION,
        'students': grouped,
    })


@require_GET
def api_student_photo(request, student_id):
    """Serve a student's profile picture (works even when DEBUG=False / no media route)."""
    if not request.user.is_authenticated:
        return _json_error('Not authenticated', 403)
    teacher = get_teacher(request)
    if not teacher:
        return _json_error('No teacher profile for this account', 403)

    student = get_object_or_404(StudentProfile, id=student_id)
    if not student.profile_picture:
        return _json_error('No profile photo', 404)
    if student.student_class and not _can_access_class(request.user, teacher, student.student_class):
        return _json_error('You do not have access to this student', 403)

    student.profile_picture.open('rb')
    content_type = (
        mimetypes.guess_type(student.profile_picture.name)[0] or 'application/octet-stream'
    )
    response = FileResponse(student.profile_picture.file, content_type=content_type)
    response['Cache-Control'] = 'private, max-age=3600'
    return response


# ─────────────────────────────────────────────
# API: enrollment
# ─────────────────────────────────────────────

@require_POST
def api_enroll(request):
    """Save one or more face embeddings for a student (computed in the browser)."""
    teacher, err = _require_teacher(request)
    if err:
        return err

    data = _parse_json_body(request)
    if data is None:
        return _json_error('Invalid JSON body')

    student_id = data.get('student_id')
    raw_vectors = data.get('embeddings')
    source = data.get('source', 'capture')
    model_version = str(data.get('model_version') or DEFAULT_MODEL_VERSION)[:40]
    if source not in ('photo', 'capture'):
        source = 'capture'
    try:
        quality = float(data.get('quality') or 0)
    except (TypeError, ValueError):
        quality = 0

    if not student_id:
        return _json_error('student_id is required')
    if not isinstance(raw_vectors, list) or not raw_vectors:
        return _json_error('embeddings must be a non-empty list of vectors')

    student = get_object_or_404(StudentProfile, id=student_id)
    if student.student_class and not _can_access_class(request.user, teacher, student.student_class):
        return _json_error('You do not have access to this student', 403)

    vectors = []
    for raw in raw_vectors:
        try:
            vectors.append(normalize_embedding(raw))
        except ValueError as exc:
            return _json_error(f'Bad embedding: {exc}')

    created = 0
    for vec in vectors:
        FaceEmbedding.objects.create(
            student=student,
            school=getattr(student, 'school', None),
            embedding=vec,
            source=source,
            quality=quality,
            model_version=model_version,
        )
        created += 1

    total = trim_embeddings(student.id)
    return JsonResponse({'ok': True, 'student_id': student.id, 'created': created, 'total': total})


@require_POST
def api_enroll_delete(request, student_id):
    """Remove all embeddings for a student."""
    teacher, err = _require_teacher(request)
    if err:
        return err

    student = get_object_or_404(StudentProfile, id=student_id)
    if student.student_class and not _can_access_class(request.user, teacher, student.student_class):
        return _json_error('You do not have access to this student', 403)

    deleted, _ = FaceEmbedding.objects.filter(student=student).delete()
    return JsonResponse({'ok': True, 'student_id': student.id, 'deleted': deleted})


# ─────────────────────────────────────────────
# API: save attendance (teacher-verified)
# ─────────────────────────────────────────────

@require_POST
def api_attendance_save(request):
    """Save the teacher-verified review table as Attendance rows (source='ai')."""
    teacher, err = _require_teacher(request)
    if err:
        return err

    data = _parse_json_body(request)
    if data is None:
        return _json_error('Invalid JSON body')

    class_id = data.get('class_id')
    subject_id = data.get('subject_id')
    date_str = data.get('date')
    statuses = data.get('statuses')
    meta = data.get('meta') or {}

    if not class_id or not subject_id:
        return _json_error('class_id and subject_id are required')
    if not isinstance(statuses, dict) or not statuses:
        return _json_error('statuses must be a non-empty object of student_id -> status')

    cls = get_object_or_404(Class, id=class_id)
    if not _can_access_class(request.user, teacher, cls):
        return _json_error('You do not have access to this class', 403)

    subject = get_object_or_404(Subject, id=subject_id)

    try:
        date = parse_iso_date(date_str or timezone.now().date())
    except ValueError:
        return _json_error('date must be in YYYY-MM-DD format')

    valid_student_ids = set(
        StudentProfile.objects.filter(student_class=cls).values_list('id', flat=True)
    )

    parsed = {}
    for key, value in statuses.items():
        try:
            sid = int(key)
        except (TypeError, ValueError):
            return _json_error(f'Invalid student id: {key!r}')
        if sid not in valid_student_ids:
            return _json_error(f'Student {sid} is not in this class')
        if value not in ALLOWED_STATUSES:
            return _json_error(f'Invalid status: {value!r}')
        parsed[sid] = value

    recognized = int(meta.get('recognized') or 0)
    unrecognized = int(meta.get('unrecognized') or 0)
    spoof_blocked = int(meta.get('spoof_blocked') or 0)

    saved = save_attendance_statuses(
        teacher=teacher,
        cls=cls,
        subject=subject,
        date=date,
        statuses=parsed,
        source='ai',
        results={str(k): v for k, v in parsed.items()},
        recognized=recognized,
        unrecognized=unrecognized,
        spoof_blocked=spoof_blocked,
    )

    return JsonResponse({'ok': True, 'saved': saved})
