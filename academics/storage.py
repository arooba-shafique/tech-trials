"""Database-backed file storage.

Vercel serverless functions have a read-only filesystem, so uploads cannot be
written to MEDIA_ROOT at runtime. File contents are stored base64-encoded in
the StoredFile table instead. Legacy files that already exist on disk (e.g.
the git-tracked demo photos) keep working through a FileSystemStorage
fallback for reads and URLs.
"""

import base64
import mimetypes

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, Storage


class DatabaseStorage(Storage):
    """Persist file bytes in the database (see StoredFile)."""

    def _legacy(self):
        return FileSystemStorage()

    def _row(self, name):
        from .models import StoredFile
        return StoredFile.objects.filter(name=name).first()

    def _open(self, name, mode='rb'):
        row = self._row(name)
        if row is not None:
            return ContentFile(base64.b64decode(row.data), name=name)
        return self._legacy()._open(name, mode)

    def _save(self, name, content):
        from .models import StoredFile
        raw = content.read()
        StoredFile.objects.update_or_create(
            name=name,
            defaults={
                'data': base64.b64encode(raw).decode('ascii'),
                'size': len(raw),
                'content_type': (
                    mimetypes.guess_type(name)[0] or 'application/octet-stream'
                ),
            },
        )
        return name

    def exists(self, name):
        return self._row(name) is not None or self._legacy().exists(name)

    def delete(self, name):
        from .models import StoredFile
        StoredFile.objects.filter(name=name).delete()
        legacy = self._legacy()
        if legacy.exists(name):
            legacy.delete(name)

    def size(self, name):
        row = self._row(name)
        if row is not None:
            return row.size
        return self._legacy().size(name)

    def url(self, name):
        if self._row(name) is not None:
            from django.utils.encoding import filepath_to_uri
            return '/db-media/' + filepath_to_uri(name)
        return self._legacy().url(name)
