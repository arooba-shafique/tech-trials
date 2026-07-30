from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import landing_page
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page, name='landing_page'),
    path('', include('accounts.urls')),
    path('', include('academics.urls')),
    path('hr/', include('hr.urls')),
    path('', include('activity.urls')),
    path('accounts/logout/', auth_views.LogoutView.as_view(
        template_name='logout.html'
    ), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
