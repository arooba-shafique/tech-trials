from django.urls import path
from . import views

urlpatterns = [
    path('activity/dashboard/', views.activity_dashboard, name='activity_dashboard'),
]
