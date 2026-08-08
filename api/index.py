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

_migrations_run = False

def setup_database():
    """Run migrations on cold start"""
    global _migrations_run
    if _migrations_run:
        return
    from django.core.management import call_command
    
    try:
        print("[setup] Running migrations...")
        call_command('migrate', verbosity=0)
        print("[setup] Migrations completed successfully.")
        _migrations_run = True
    except Exception as e:
        print(f"[setup] Migration error: {e}")
        import traceback
        traceback.print_exc()

# Run setup on import (cold start)
setup_database()

# Get the WSGI application
application = StaticFilesHandler(get_wsgi_application())

# For Vercel serverless functions
if __name__ == "__main__":
    application()
