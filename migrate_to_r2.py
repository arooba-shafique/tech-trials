"""
Migration script to upload existing local media files to Cloudflare R2.

Usage:
    1. Set environment variables:
        export AWS_STORAGE_BUCKET_NAME=your-bucket-name
        export AWS_S3_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
        export AWS_ACCESS_KEY_ID=your-access-key
        export AWS_SECRET_ACCESS_KEY=your-secret-key

    2. Run: python migrate_to_r2.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dps_ravi.settings')

import django
django.setup()

from django.core.files.storage import default_storage
from pathlib import Path

MEDIA_ROOT = Path('dps_ravi/media')


def migrate_files():
    if not MEDIA_ROOT.exists():
        print("No local media directory found. Nothing to migrate.")
        return

    files = list(MEDIA_ROOT.rglob('*'))
    files = [f for f in files if f.is_file()]

    if not files:
        print("No files found in local media directory.")
        return

    print(f"Found {len(files)} files to migrate to R2.\n")

    uploaded = 0
    errors = 0

    for file_path in files:
        relative_path = file_path.relative_to(MEDIA_ROOT)
        remote_path = str(relative_path)

        try:
            print(f"Uploading: {remote_path}...", end=" ")
            with open(file_path, 'rb') as f:
                default_storage.save(remote_path, f)
            print("OK")
            uploaded += 1
        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

    print(f"\nMigration complete!")
    print(f"  Uploaded: {uploaded}")
    print(f"  Errors:   {errors}")


if __name__ == '__main__':
    migrate_files()
