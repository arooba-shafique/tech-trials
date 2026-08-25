from django import forms
from .models import (
    StudentProfile, TeacherProfile, ParentProfile,
    Class, Subject, TeacherSubjectAssignment, Exam, Result
)


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'full_name',
            'guardian_name',
            'date_of_birth',
            'gender',
            'profile_picture',
            'roll_number',
            'admission_number',
            'student_class',
            'admission_date',
            'phone',
            'address',
            'email',
        ]

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if school:
            self.fields['student_class'].queryset = Class.objects.filter(school=school)


class TeacherProfileForm(forms.ModelForm):
    doc_file = forms.FileField(required=False, label="Upload Document")
    doc_title = forms.CharField(required=False, max_length=100, label="Document Title")

    class Meta:
        model = TeacherProfile
        fields = [
            'full_name',
            'father_name',
            'date_of_birth',
            'gender',
            'profile_picture',
            'employee_id',
            'cnic',
            'designation',
            'employment_type',
            'skill_level',
            'subjects',
            'joining_date',
            'phone',
            'address',
            'email',
            'salary',
            'salary_type',
            'working_days_per_week',
            'bank_name',
            'bank_account',
        ]

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if school:
            self.fields['subjects'].queryset = Subject.objects.filter(school=school)


class ParentProfileForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=StudentProfile.objects.select_related('student_class').all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select Children"
    )

    class Meta:
        model = ParentProfile
        fields = ['full_name', 'relation', 'phone', 'students', 'email']

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if school:
            self.fields['students'].queryset = StudentProfile.objects.filter(school=school).select_related('student_class')
        self.fields['students'].label_from_instance = lambda s: f"{s.full_name} — {s.student_class or 'No Class Assigned'}"




class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'section', 'academic_year', 'class_teacher']

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if school:
            self.fields['class_teacher'].queryset = TeacherProfile.objects.filter(school=school)


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code']


class TeacherSubjectAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeacherSubjectAssignment
        fields = ['teacher', 'subject', 'assigned_class', 'academic_year']

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if school:
            self.fields['teacher'].queryset = TeacherProfile.objects.filter(school=school)
            self.fields['subject'].queryset = Subject.objects.filter(school=school)
            self.fields['assigned_class'].queryset = Class.objects.filter(school=school)


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'subject', 'assigned_class', 'exam_date', 'total_marks', 'passing_marks']
        # created_by excluded — set automatically from request.user in the view


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['student', 'exam', 'marks_obtained']
        # uploaded_by excluded — set automatically from request.user in the view
