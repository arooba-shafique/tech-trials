import math
from datetime import date as date_cls

from academics.models import Attendance, StudentProfile

from .models import AISession, FaceEmbedding

MAX_EMBEDDINGS_PER_STUDENT = 10
EMBEDDING_MIN_DIM = 32
EMBEDDING_MAX_DIM = 1024

ALLOWED_STATUSES = {'present', 'absent', 'leave'}
DEFAULT_MODEL_VERSION = 'arcface-mbf-v1'

MATCH_THRESHOLD = 0.50
MIN_FACE_SIDE = 90
TRACK_MIN_VOTES = 2
SPOOF_REAL_THRESHOLD = 0.5


def normalize_embedding(values):
    """Validate a raw embedding list and return an L2-normalized copy.

    Raises ValueError with a human-readable message on bad input.
    """
    if not isinstance(values, (list, tuple)):
        raise ValueError('embedding must be a list of numbers')
    if not (EMBEDDING_MIN_DIM <= len(values) <= EMBEDDING_MAX_DIM):
        raise ValueError(
            f'embedding must have {EMBEDDING_MIN_DIM}-{EMBEDDING_MAX_DIM} values, got {len(values)}'
        )
    try:
        vec = [float(v) for v in values]
    except (TypeError, ValueError):
        raise ValueError('embedding contains non-numeric values')
    if any(not math.isfinite(v) for v in vec):
        raise ValueError('embedding contains NaN or Inf values')
    norm = math.sqrt(sum(v * v for v in vec))
    if norm < 1e-6:
        raise ValueError('embedding has zero magnitude')
    return [v / norm for v in vec]


def parse_iso_date(value):
    """Parse 'YYYY-MM-DD'. Raises ValueError on bad input."""
    return date_cls.fromisoformat(str(value))


def save_attendance_statuses(*, teacher, cls, subject, date, statuses, source,
                             results=None, recognized=0, unrecognized=0, spoof_blocked=0):
    """Upsert Attendance rows (same semantics as the manual mark flow) and log an AISession.

    `statuses` must be {student_pk: 'present'|'absent'|'leave'} for students of `cls`.
    Returns the number of records written.
    """
    saved = 0
    for student_id, status in statuses.items():
        if not StudentProfile.objects.filter(id=student_id, student_class=cls).exists():
            continue
        Attendance.objects.update_or_create(
            student_id=student_id,
            subject=subject,
            date=date,
            defaults={
                'student_class': cls,
                'marked_by': teacher,
                'status': status,
                'source': source,
            },
        )
        saved += 1

    AISession.objects.create(
        teacher=teacher,
        school=getattr(teacher, 'school', None),
        student_class=cls,
        subject=subject,
        date=date,
        results=results if results is not None else {},
        recognized_count=recognized,
        unrecognized_count=unrecognized,
        spoof_blocked_count=spoof_blocked,
    )
    return saved


def trim_embeddings(student_id):
    """Keep only the newest MAX_EMBEDDINGS_PER_STUDENT embeddings. Returns total kept."""
    ids = list(
        FaceEmbedding.objects.filter(student_id=student_id)
        .order_by('-created_at')
        .values_list('id', flat=True)
    )
    for old_id in ids[MAX_EMBEDDINGS_PER_STUDENT:]:
        FaceEmbedding.objects.filter(id=old_id).delete()
    return min(len(ids), MAX_EMBEDDINGS_PER_STUDENT)
