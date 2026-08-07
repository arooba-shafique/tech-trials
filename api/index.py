import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dps_ravi.settings')

# Import Django and initialize
import django
django.setup()

from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

# Run migrations and create superuser on cold start
def setup_database():
    """Run migrations and create superuser on cold start"""
    from django.core.management import call_command
    from django.contrib.auth import get_user_model
    
    try:
        print("Running migrations...")
        call_command('migrate', verbosity=1)
        print("Migrations completed.")
    except Exception as e:
        print(f"Migration error: {e}")
        import traceback
        traceback.print_exc()
    
    # Create superuser if it doesn't exist
    try:
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            print("Creating admin superuser...")
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='admin',
                is_staff=True,
                is_superuser=True
            )
            print("Admin superuser created.")
        else:
            print("Admin superuser already exists.")
    except Exception as e:
        print(f"Error creating superuser: {e}")

# Run setup on import (cold start)
setup_database()

# Get the WSGI application
application = StaticFilesHandler(get_wsgi_application())

# For Vercel serverless functions
if __name__ == "__main__":
    application()
