from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Class(models.Model):
    name = models.CharField(max_length=10)
    section = models.CharField(max_length=10)
    academic_year = models.CharField(max_length=20, default='2024-2025')
    school = models.ForeignKey(
        'accounts.School', on_delete=models.CASCADE, null=True, blank=True,
        related_name='classes'
    )
    class_teacher = models.ForeignKey(
        'TeacherProfile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_class'
    )

    class Meta:
        unique_together = ('name', 'section', 'academic_year')
        verbose_name_plural = 'Classes'
        ordering = ['name', 'section']

    def __str__(self):
        return f"{self.name} - {self.section} [{self.academic_year}]"


class Subject(models.Model):
    name = models.CharField(max_length=100) 
    code = models.CharField(max_length=20, unique=True)
    school = models.ForeignKey(
        'accounts.School', on_delete=models.CASCADE, null=True, blank=True,
        related_name='subjects'
    )

    def __str__(self):
        return f"{self.name} ({self.code})"


class StudentProfile(models.Model):
    email = models.EmailField(blank=True, null=True)
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    school = models.ForeignKey(
        'accounts.School', on_delete=models.CASCADE, null=True, blank=True,
        related_name='students'
    )

    full_name = models.CharField(max_length=100)
    guardian_name = models.CharField(max_length=100)

    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    profile_picture = models.ImageField(upload_to='students/pictures/', null=True, blank=True)

    roll_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    admission_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    student_class = models.ForeignKey('Class', on_delete=models.SET_NULL, null=True)
    admission_date = models.DateField(default=timezone.now)

    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        base = f"{self.full_name} ({self.admission_number})"
        email = self.email or (self.user.email if self.user else None)
        if email:
            return f"{base} - {email}"
        return base



class TeacherProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    DESIGNATION_CHOICES = (
        ('teacher', 'Teacher'),
        ('coordinator', 'Coordinator'),
        ('manager', 'Manager'),
        ('vp', 'VP'),
        ('group_head', 'Group Head'),
    )
    EMPLOYMENT_TYPE_CHOICES = (
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('daily_wager', 'Daily Wager'),
    )
    SKILL_LEVEL_CHOICES = (
        ('permanent_professional', 'Permanent Professional'),
        ('skilled', 'Skilled'),
        ('semi_skilled', 'Semi Skilled'),
        ('unskilled', 'Unskilled'),
    )
    SALARY_TYPE_CHOICES = (
        ('monthly', 'Monthly'),
        ('daily', 'Daily'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='teacher_profile'
    )
    school = models.ForeignKey(
        'accounts.School', on_delete=models.CASCADE, null=True, blank=True,
        related_name='teachers'
    )

    full_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    profile_picture = models.ImageField(upload_to='teachers/pictures/', null=True, blank=True)

    employee_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    cnic = models.CharField(max_length=20, blank=True, default='')
    designation = models.CharField(max_length=25, choices=DESIGNATION_CHOICES, default='teacher', blank=True)
    employment_type = models.CharField(max_length=15, choices=EMPLOYMENT_TYPE_CHOICES, default='permanent', blank=True)
    skill_level = models.CharField(max_length=25, choices=SKILL_LEVEL_CHOICES, default='permanent_professional', blank=True)
    subjects = models.ManyToManyField('Subject', blank=True, related_name='teachers')
    joining_date = models.DateField(null=True, blank=True)

    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True, null=True)

    # Salary fields
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Basic Monthly/Daily Salary")
    salary_type = models.CharField(max_length=10, choices=SALARY_TYPE_CHOICES, default='monthly', blank=True)
    working_days_per_week = models.PositiveIntegerField(default=6)
    is_employee_separated = models.BooleanField(default=False, help_text="Has the employee left?")
    bank_account = models.CharField(max_length=50, blank=True, default='')
    bank_name = models.CharField(max_length=100, blank=True, default='')
    documents_json = models.TextField(blank=True, default='[]', help_text="JSON array of staff documents")

    def __str__(self):
        base = f"{self.full_name} ({self.employee_id})"
        email = self.email or (self.user.email if self.user else None)
        if email:
            return f"{base} - {email}"
        return base

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"

class ParentProfile(models.Model):
    email = models.EmailField(blank=True, null=True)
    RELATION_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='parent_profile'
    )
    school = models.ForeignKey(
        'accounts.School', on_delete=models.CASCADE, null=True, blank=True,
        related_name='parents'
    )
    full_name = models.CharField(max_length=100)
    relation = models.CharField(max_length=10, choices=RELATION_CHOICES, default='father')
    phone = models.CharField(max_length=15, blank=True)

    students = models.ManyToManyField('StudentProfile', related_name='parents', blank=True)

    def __str__(self):
        base = f"{self.full_name} ({self.get_relation_display()})"
        email = self.email or (self.user.email if self.user else None)
        if email:
            return f"{base} - {email}"
        return base

    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"

class TeacherSubjectAssignment(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    assigned_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='assignments')
    academic_year = models.CharField(max_length=20, default='2024-2025')

    class Meta:
        unique_together = ('teacher', 'subject', 'assigned_class', 'academic_year')
        verbose_name = "Teacher Subject Assignment"
        verbose_name_plural = "Teacher Subject Assignments"

    def __str__(self):
        return f"{self.teacher} → {self.subject} ({self.assigned_class})"
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendances')
    student_class = models.ForeignKey('Class', on_delete=models.SET_NULL, null=True, related_name='attendances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendances')
    marked_by = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, related_name='marked_attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')

    class Meta:
        unique_together = ('student', 'subject', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} - {self.student_class} - {self.subject} - {self.date} ({self.get_status_display()})"

class Exam(models.Model):

    name = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    assigned_class = models.ForeignKey('Class', on_delete=models.CASCADE, related_name='exams')
    created_by = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, related_name='created_exams')
    exam_date = models.DateField()
    total_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=40)

    class Meta:
        unique_together = ('subject', 'assigned_class', 'exam_date')
        ordering = ['-exam_date']

    def __str__(self):
        return f"{self.name} - {self.subject} ({self.assigned_class})"

class Result(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='results')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    marks_obtained = models.FloatField()
    uploaded_by = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, related_name='uploaded_results')

    class Meta:
        unique_together = ('student', 'exam')
        ordering = ['-exam__exam_date']

    @property
    def percentage(self):
        return round((self.marks_obtained / self.exam.total_marks) * 100, 2)

    @property
    def is_passing(self):
        return self.marks_obtained >= self.exam.passing_marks

    def __str__(self):
        return f"{self.student} - {self.exam} - {self.marks_obtained}/{self.exam.total_marks}"
class HomeTask(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_class = models.ForeignKey('Class', on_delete=models.CASCADE, related_name='hometasks')
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='hometasks')
    assigned_by = models.ForeignKey('TeacherProfile', on_delete=models.SET_NULL, null=True, related_name='hometasks')
    assigned_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    attachment = models.FileField(upload_to='hometasks/', null=True, blank=True)

    class Meta:
        ordering = ['-assigned_date']

    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date()

    def __str__(self):
        return f"{self.title} – {self.assigned_class}"
    
class TimetableSlot(models.Model):
    DAY_CHOICES = [
        ('Monday','Monday'), ('Tuesday','Tuesday'), ('Wednesday','Wednesday'),
        ('Thursday','Thursday'), ('Friday','Friday'), ('Saturday','Saturday'),
    ]
    assigned_class = models.ForeignKey('Class', on_delete=models.CASCADE, related_name='timetable_slots')
    subject        = models.ForeignKey('Subject', on_delete=models.CASCADE)
    teacher        = models.ForeignKey('TeacherProfile', on_delete=models.SET_NULL, null=True, blank=True)
    day            = models.CharField(max_length=10, choices=DAY_CHOICES)
    period_number  = models.PositiveSmallIntegerField()
    start_time     = models.TimeField()
    end_time       = models.TimeField()
    duration       = models.PositiveSmallIntegerField(default=45)

    class Meta:
        ordering = ['day', 'period_number']
        unique_together = ['assigned_class', 'day', 'period_number']

@property
def period_label(self):
    return f"P{self.period_number}"
