from django.urls import path

from . import views

urlpatterns = [
    # Pages
    path('teacher/ai-attendance/', views.ai_session_page, name='ai_attendance_session'),
    path('teacher/ai-attendance/enroll/', views.ai_enroll_page, name='ai_attendance_enroll'),

    # API
    path('api/ai/class/<int:class_id>/', views.api_class_roster, name='ai_api_class_roster'),
    path('api/ai/embeddings/<int:class_id>/', views.api_class_embeddings, name='ai_api_class_embeddings'),
    path('api/ai/photo/<int:student_id>/', views.api_student_photo, name='ai_api_student_photo'),
    path('api/ai/enroll/', views.api_enroll, name='ai_api_enroll'),
    path('api/ai/enroll/<int:student_id>/delete/', views.api_enroll_delete, name='ai_api_enroll_delete'),
    path('api/ai/attendance/save/', views.api_attendance_save, name='ai_api_attendance_save'),
]
