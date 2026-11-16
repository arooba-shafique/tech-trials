from django.db import models


class FaceEmbedding(models.Model):
    """A face embedding (ArcFace vector) for a student, computed in the browser."""

    SOURCE_CHOICES = [
        ('photo', 'Profile Photo'),
        ('capture', 'Camera Capture'),
    ]

    student = models.ForeignKey(
        'academics.StudentProfile',
        on_delete=models.CASCADE,
        related_name='face_embeddings',
    )
    school = models.ForeignKey(
        'accounts.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='face_embeddings',
    )
    embedding = models.JSONField(help_text='L2-normalized float vector (e.g. 512 values)')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='photo')
    quality = models.FloatField(default=0)
    model_version = models.CharField(max_length=40, default='arcface-mbf-v1')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"FaceEmbedding({self.student_id}, {self.model_version}, {self.source})"


class AISession(models.Model):
    """Log of one AI attendance session (what the AI suggested and what was saved)."""

    teacher = models.ForeignKey(
        'academics.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='ai_attendance_sessions',
    )
    school = models.ForeignKey(
        'accounts.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ai_attendance_sessions',
    )
    student_class = models.ForeignKey(
        'academics.Class',
        on_delete=models.CASCADE,
        related_name='ai_sessions',
    )
    subject = models.ForeignKey(
        'academics.Subject',
        on_delete=models.CASCADE,
        related_name='ai_sessions',
    )
    date = models.DateField()
    results = models.JSONField(default=dict, blank=True)
    recognized_count = models.PositiveIntegerField(default=0)
    unrecognized_count = models.PositiveIntegerField(default=0)
    spoof_blocked_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"AISession({self.student_class} {self.subject} {self.date})"
