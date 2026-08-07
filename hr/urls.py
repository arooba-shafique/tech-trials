from django.urls import path
from . import views

urlpatterns = [
    path('employees/', views.employee_list, name='hr_employee_list'),
    path('employee/<int:employee_id>/', views.employee_detail, name='hr_employee_detail'),
    path('employee/<int:employee_id>/edit/', views.employee_edit, name='hr_employee_edit'),
    path('employee/<int:employee_id>/delete/', views.employee_delete, name='hr_employee_delete'),
    path('employee/<int:employee_id>/salary/add/', views.add_employee_salary, name='hr_add_employee_salary'),
    path('employee/<int:employee_id>/salary/edit/', views.edit_employee_salary, name='hr_edit_employee_salary'),
    path('employee/<int:employee_id>/salary/delete/', views.delete_employee_salary, name='hr_delete_employee_salary'),
    path('salary-config/', views.salary_config, name='hr_salary_config'),
    path('salary-config/save-overrides/', views.save_employee_overrides, name='hr_save_employee_overrides'),
    path('salary/generate/', views.generate_monthly_salary, name='hr_generate_salary'),
    path('salary/monthly/', views.monthly_salary_list, name='hr_monthly_salary_list'),
    path('salary/<int:pk>/edit/', views.edit_monthly_salary, name='hr_edit_monthly_salary'),
    path('salary/<int:pk>/delete/', views.delete_monthly_salary, name='hr_delete_monthly_salary'),
    path('salary/<int:pk>/slip/', views.salary_slip, name='hr_salary_slip'),
    path('salary/<int:pk>/slip/pdf/', views.salary_slip_pdf, name='hr_salary_slip_pdf'),
    path('salary/slip/all/', views.salary_slip_all, name='hr_salary_slip_all'),
    path('salary/export/csv/', views.export_salary_csv, name='hr_export_salary_csv'),
    path('attendance/monthly/', views.monthly_attendance_summary, name='hr_monthly_attendance'),
    path('employee/<int:employee_id>/upload-doc/', views.upload_employee_document, name='hr_upload_employee_document'),
    path('document/<int:doc_id>/delete/', views.delete_employee_document, name='hr_delete_employee_document'),
    path('document/<int:doc_id>/download/', views.download_employee_document, name='hr_download_employee_document'),
]
