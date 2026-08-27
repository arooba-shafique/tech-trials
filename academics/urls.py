from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin-console/', views.admin_dashboard, name='admin_console'),
path('teacher/login/',views.teacher_login, name='teacher_login'),
path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
path('teacher/logout/', views.teacher_logout, name='teacher_logout'),
    # ─────────── STUDENT ───────────
    path('add/student/', views.add_student, name='add_student'),
    path('edit/student/<int:pk>/', views.edit_student, name='edit_student'),
    path('delete/student/<int:pk>/', views.delete_student, name='delete_student'),

    # ─────────── TEACHER ───────────
    path('add/teacher/', views.add_teacher, name='add_teacher'),
    path('edit/teacher/<int:pk>/', views.edit_teacher, name='edit_teacher'),
    path('delete/teacher/<int:pk>/', views.delete_teacher, name='delete_teacher'),
    path('staff/<int:pk>/documents/', views.staff_documents, name='staff_documents'),
    path('staff/<int:pk>/documents/add/', views.add_staff_document, name='add_staff_document'),
    path('staff/<int:pk>/documents/<str:doc_id>/delete/', views.delete_staff_document, name='delete_staff_document'),
    path('staff/<int:pk>/documents/<str:doc_id>/download/', views.download_staff_document, name='download_staff_document'),
    path('teacher/password-reset/', views.teacher_password_reset, name='teacher_password_reset'),
    path('teacher/password-change/', views.teacher_password_reset, name='teacher_password_change'),
    path('accounts/teacher/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
    template_name='password_reset_confirm.html',
    success_url='/teacher/login/?msg=reset_done'
), name='teacher_password_reset_confirm'),

    # ─────────── PARENT ───────────
    path('add/parent/', views.add_parent, name='add_parent'),
    path('edit/parent/<int:pk>/', views.edit_parent, name='edit_parent'),
    path('delete/parent/<int:pk>/', views.delete_parent, name='delete_parent'),
    path('delete/parent/<int:pk>/', views.delete_parent, name='delete_parent'),
    path('parent/login/', views.parent_login, name='parent_login'),
    path('parent/', views.parent_dashboard,  name='parent_dashboard'),
    path('parent/logout/', views.parent_logout, name='parent_logout'),


    # ─────────── CLASS ───────────
    path('add/class/', views.add_class, name='add_class'),
    path('edit/class/<int:pk>/', views.edit_class, name='edit_class'),
    path('delete/class/<int:pk>/', views.delete_class, name='delete_class'),

    # ─────────── SUBJECT ───────────
    path('add/subject/', views.add_subject, name='add_subject'),
    path('edit/subject/<int:pk>/', views.edit_subject, name='edit_subject'),
    path('delete/subject/<int:pk>/', views.delete_subject, name='delete_subject'),

    # ─────────── ASSIGNMENT ───────────
    path('add/assignment/', views.add_assignment, name='add_assignment'),
    path('delete/assignment/<int:pk>/', views.delete_assignment, name='delete_assignment'),
    path('assignment/<int:pk>/edit/', views.edit_assignment, name='edit_assignment'),

    # Add inside urlpatterns:
path('api/subjects-by-class/<int:class_id>/', views.subjects_by_class, name='subjects_by_class'),
    path('teacher/attendance/mark/', views.teacher_mark_attendance, name='teacher_mark_attendance'),
    path('teacher/hometask/add/', views.teacher_add_hometask, name='teacher_add_hometask'),
    path('teacher/hometask/<int:pk>/edit/', views.teacher_edit_hometask, name='teacher_edit_hometask'),
    path('teacher/hometask/<int:pk>/delete/', views.teacher_delete_hometask, name='teacher_delete_hometask'),
    path('teacher/exam/add/', views.teacher_add_exam, name='teacher_add_exam'),
    path('teacher/exam/<int:pk>/edit/', views.teacher_edit_exam, name='teacher_edit_exam'),
    path('teacher/exam/<int:pk>/delete/', views.teacher_delete_exam, name='teacher_delete_exam'),
    path('teacher/result/add/', views.teacher_add_result, name='teacher_add_result'),
    path('timetable/save/',  views.save_timetable,    name='timetable_save'),
    path('timetable/load/',  views.load_timetable,    name='timetable_load'),
    path('timetable/clear/', views.clear_timetable,   name='timetable_clear'),
path('student/login/',     views.student_login,     name='student_login'),
path('student/logout/',    views.student_logout,    name='student_logout'),
path('student_dashboard/',           views.student_dashboard, name='student_dashboard'),
path('credentials/generate/', views.generate_credentials, name='generate_credentials'),

path('credentials/generate/', views.generate_credentials, name='generate_credentials'),

    # ─────────── DATA IMPORT / EXPORT ───────────
    path('data/export/', views.export_data, name='data_export'),
    path('data/import/', views.import_data, name='data_import'),
]
