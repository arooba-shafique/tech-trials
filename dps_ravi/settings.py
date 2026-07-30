from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ Secret key - from environment variable
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-r=zbwsre=)m72*ks4aaz78^smv#lq(vebp02z=hs#xovsdrtg+')

# ✅ Debug mode - False in production
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

# ✅ Allowed hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# ✅ CSRF trusted origins for Vercel
CSRF_TRUSTED_ORIGINS = [
    'https://arooba.pythonanywhere.com',
    'https://vercel.app',
    'https://*.vercel.app',
]
# Add custom domain if provided
custom_domain = os.environ.get('CUSTOM_DOMAIN')
if custom_domain:
    CSRF_TRUSTED_ORIGINS.append(f'https://{custom_domain}')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'academics',
    'hr',
    'activity',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'dps_ravi.middleware.TrialExpiryMiddleware',
    'activity.middleware.ActivityTrackingMiddleware',
]

ROOT_URLCONF = 'dps_ravi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dps_ravi.wsgi.application'

# ✅ Database configuration
# Use PostgreSQL in production if DATABASE_URL is provided, otherwise SQLite for development
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # PostgreSQL for production (Vercel, Railway, etc.)
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Karachi'
USE_I18N = True
USE_TZ = True

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'dps_ravi', 'media')

# ✅ Static files configuration for Vercel
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'dps_ravi' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# ✅ WhiteNoise configuration
WHITENOISE_KEEP_APP_FILES = True
WHITENOISE_USE_FINDERS = True

# ✅ Custom user model
AUTH_USER_MODEL = 'accounts.User'

# ✅ Email credentials - from environment variables
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'nafiaaziz.500@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'qlyd mflf lbsp lwes')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

LOGIN_URL = 'teacher_login'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGOUT_REDIRECT_URL = '/'

# ✅ Vercel-specific settings
VERCEL = os.environ.get('VERCEL', False)
if VERCEL:
    # Use environment variables for sensitive data in production
    SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)
    DEBUG = False
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')
