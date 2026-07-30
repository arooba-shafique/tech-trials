from django.urls import path
from . import views

urlpatterns = [
    path('activity/dashboard/', views.activity_dashboard, name='activity_dashboard'),
    path('activity/force-logout/<str:session_key>/', views.force_logout, name='force_logout'),
]
