import os
import tempfile

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import School, User
from .models import Class, StoredFile, StudentProfile
from .storage import DatabaseStorage

TINY_GIF = (
    b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
    b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


class DatabaseStorageTests(TestCase):
    def setUp(self):
        self.storage = DatabaseStorage()

    def test_save_and_open_roundtrip(self):
        name = self.storage.save('students/pictures/rt.gif', ContentFile(TINY_GIF))
        self.assertTrue(self.storage.exists(name))
        with self.storage.open(name) as fh:
            self.assertEqual(fh.read(), TINY_GIF)
        self.assertEqual(self.storage.size(name), len(TINY_GIF))
        self.assertTrue(StoredFile.objects.filter(name=name).exists())

    def test_url_points_at_db_media_route(self):
        name = self.storage.save('students/pictures/u.gif', ContentFile(TINY_GIF))
        self.assertEqual(self.storage.url(name), '/db-media/students/pictures/u.gif')

    def test_duplicate_name_gets_unique(self):
        a = self.storage.save('students/pictures/dup.gif', ContentFile(TINY_GIF))
        b = self.storage.save('students/pictures/dup.gif', ContentFile(TINY_GIF))
        self.assertNotEqual(a, b)
        with self.storage.open(b) as fh:
            self.assertEqual(fh.read(), TINY_GIF)

    def test_legacy_disk_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            rel = 'students/pictures/legacy.gif'
            path = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as fh:
                fh.write(TINY_GIF)
            with override_settings(MEDIA_ROOT=tmp):
                self.assertTrue(self.storage.exists(rel))
                with self.storage.open(rel) as fh:
                    self.assertEqual(fh.read(), TINY_GIF)
                self.assertEqual(self.storage.url(rel), '/media/' + rel)

    def test_delete_removes_row(self):
        name = self.storage.save('students/pictures/del.gif', ContentFile(TINY_GIF))
        self.storage.delete(name)
        self.assertFalse(self.storage.exists(name))
        self.assertFalse(StoredFile.objects.filter(name=name).exists())


class ServeStoredFileTests(TestCase):
    def test_serves_bytes_with_content_type(self):
        name = DatabaseStorage().save(
            'students/pictures/s.gif', ContentFile(TINY_GIF)
        )
        resp = self.client.get(reverse('serve_stored_file', args=[name]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, TINY_GIF)
        self.assertTrue(resp['Content-Type'].startswith('image/'))

    def test_404_when_unknown(self):
        resp = self.client.get(
            reverse('serve_stored_file', args=['no/such/file.gif'])
        )
        self.assertEqual(resp.status_code, 404)


class AddStudentPhotoTests(TestCase):
    """End-to-end: admin adds a student with a photo -> photo persists."""

    def setUp(self):
        self.school = School.objects.create(name='Test School')
        self.admin = User.objects.create_user(
            username='boss', password='pw', role='admin', school=self.school
        )
        self.cls = Class.objects.create(
            name='5', section='A', academic_year='2024-2025', school=self.school
        )
        self.client.login(username='boss', password='pw')

    def test_photo_upload_persists_to_database(self):
        photo = SimpleUploadedFile('kid.gif', TINY_GIF, content_type='image/gif')
        resp = self.client.post(reverse('add_student'), {
            'full_name': 'New Kid',
            'guardian_name': 'Guardian',
            'date_of_birth': '2015-05-05',
            'gender': 'M',
            'roll_number': 'R900',
            'admission_number': 'ADM900',
            'student_class': str(self.cls.id),
            'admission_date': '2024-09-01',
            'phone': '1',
            'address': 'x',
            'email': '',
            'profile_picture': photo,
        })
        self.assertEqual(resp.status_code, 302)

        student = StudentProfile.objects.get(roll_number='R900')
        self.assertTrue(student.profile_picture)
        self.assertTrue(
            StoredFile.objects.filter(name=student.profile_picture.name).exists()
        )

        served = self.client.get(
            reverse('serve_stored_file', args=[student.profile_picture.name])
        )
        self.assertEqual(served.status_code, 200)
        self.assertEqual(served.content, TINY_GIF)
