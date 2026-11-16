import json
import tempfile
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import School, User
from academics.models import Class, StudentProfile, Subject, TeacherProfile, TeacherSubjectAssignment, Attendance
from aiattendance.models import AISession, FaceEmbedding

TINY_GIF = (
    b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
    b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)

VEC_512 = [0.01] * 512


def _json(response):
    return json.loads(response.content.decode('utf-8'))


class AIAttendanceAPITests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Test School')
        self.user = User.objects.create_user(
            username='t1', password='pw', role='teacher', school=self.school
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.user, full_name='Test Teacher', school=self.school
        )
        self.cls = Class.objects.create(
            name='5', section='A', academic_year='2024-2025',
            school=self.school, class_teacher=self.teacher,
        )
        self.subject = Subject.objects.create(name='Math', code='M1', school=self.school)
        TeacherSubjectAssignment.objects.create(
            teacher=self.teacher, subject=self.subject,
            assigned_class=self.cls, academic_year='2024-2025',
        )
        self.s1 = StudentProfile.objects.create(
            full_name='Ali', date_of_birth=date(2015, 1, 1),
            student_class=self.cls, school=self.school, roll_number='R1',
        )
        self.s2 = StudentProfile.objects.create(
            full_name='Sara', date_of_birth=date(2015, 2, 1),
            student_class=self.cls, school=self.school, roll_number='R2',
        )
        self.client.login(username='t1', password='pw')

    # ── roster ──

    def test_roster_returns_students_and_subjects(self):
        resp = self.client.get(reverse('ai_api_class_roster', args=[self.cls.id]))
        self.assertEqual(resp.status_code, 200)
        data = _json(resp)
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['students']), 2)
        self.assertEqual(data['subjects'][0]['id'], self.subject.id)
        self.assertEqual(data['students'][0]['enrolled'], 0)

    def test_roster_denied_for_other_teacher(self):
        user2 = User.objects.create_user(username='t2', password='pw', role='teacher')
        TeacherProfile.objects.create(user=user2, full_name='Other')
        self.client.logout()
        self.client.login(username='t2', password='pw')
        resp = self.client.get(reverse('ai_api_class_roster', args=[self.cls.id]))
        self.assertEqual(resp.status_code, 403)

    def test_roster_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('ai_api_class_roster', args=[self.cls.id]))
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(_json(resp).get('ok'))

    # ── enrollment ──

    def test_enroll_creates_normalized_embedding(self):
        resp = self.client.post(
            reverse('ai_api_enroll'),
            data=json.dumps({
                'student_id': self.s1.id,
                'embeddings': [VEC_512],
                'source': 'capture',
                'quality': 0.9,
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = _json(resp)
        self.assertEqual(data['created'], 1)
        emb = FaceEmbedding.objects.get(student=self.s1)
        norm = sum(v * v for v in emb.embedding) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=5)
        self.assertEqual(emb.source, 'capture')

    def test_enroll_rejects_bad_embedding(self):
        resp = self.client.post(
            reverse('ai_api_enroll'),
            data=json.dumps({'student_id': self.s1.id, 'embeddings': [[1, 2, 3]]}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(FaceEmbedding.objects.count(), 0)

    def test_enroll_trims_old_embeddings(self):
        for i in range(13):
            FaceEmbedding.objects.create(student=self.s1, embedding=VEC_512)
        resp = self.client.post(
            reverse('ai_api_enroll'),
            data=json.dumps({'student_id': self.s1.id, 'embeddings': [VEC_512]}),
            content_type='application/json',
        )
        self.assertEqual(_json(resp)['total'], 10)
        self.assertEqual(FaceEmbedding.objects.filter(student=self.s1).count(), 10)

    def test_embeddings_endpoint_groups_by_student(self):
        FaceEmbedding.objects.create(student=self.s1, embedding=VEC_512, model_version='arcface-mbf-v1')
        FaceEmbedding.objects.create(student=self.s1, embedding=VEC_512, model_version='arcface-mbf-v1')
        resp = self.client.get(reverse('ai_api_class_embeddings', args=[self.cls.id]))
        data = _json(resp)
        self.assertEqual(len(data['students']), 1)
        self.assertEqual(len(data['students'][0]['vectors']), 2)

    def test_enroll_delete(self):
        FaceEmbedding.objects.create(student=self.s1, embedding=VEC_512)
        resp = self.client.post(reverse('ai_api_enroll_delete', args=[self.s1.id]))
        self.assertEqual(_json(resp)['deleted'], 1)
        self.assertEqual(FaceEmbedding.objects.count(), 0)

    # ── attendance save (teacher verification) ──

    def test_save_creates_ai_attendance_rows(self):
        payload = {
            'class_id': self.cls.id,
            'subject_id': self.subject.id,
            'date': '2026-11-15',
            'statuses': {str(self.s1.id): 'present', str(self.s2.id): 'absent'},
            'meta': {'recognized': 1, 'unrecognized': 1, 'spoof_blocked': 0},
        }
        resp = self.client.post(
            reverse('ai_api_attendance_save'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(_json(resp)['saved'], 2)

        a1 = Attendance.objects.get(student=self.s1, subject=self.subject, date=date(2026, 11, 15))
        self.assertEqual(a1.status, 'present')
        self.assertEqual(a1.source, 'ai')
        a2 = Attendance.objects.get(student=self.s2, date=date(2026, 11, 15))
        self.assertEqual(a2.status, 'absent')

        session = AISession.objects.get()
        self.assertEqual(session.recognized_count, 1)
        self.assertEqual(session.unrecognized_count, 1)

    def test_save_overwrites_previous_record(self):
        Attendance.objects.create(
            student=self.s1, student_class=self.cls, subject=self.subject,
            date=date(2026, 11, 15), status='absent', source='manual',
        )
        payload = {
            'class_id': self.cls.id,
            'subject_id': self.subject.id,
            'date': '2026-11-15',
            'statuses': {str(self.s1.id): 'present'},
        }
        self.client.post(
            reverse('ai_api_attendance_save'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(Attendance.objects.filter(student=self.s1).count(), 1)
        self.assertEqual(
            Attendance.objects.get(student=self.s1).status, 'present'
        )

    def test_save_rejects_invalid_status(self):
        payload = {
            'class_id': self.cls.id,
            'subject_id': self.subject.id,
            'date': '2026-11-15',
            'statuses': {str(self.s1.id): 'maybe'},
        }
        resp = self.client.post(
            reverse('ai_api_attendance_save'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Attendance.objects.count(), 0)

    def test_save_rejects_student_not_in_class(self):
        other_cls = Class.objects.create(name='6', section='B', academic_year='2024-2025')
        outsider = StudentProfile.objects.create(
            full_name='Z', date_of_birth=date(2014, 1, 1), student_class=other_cls
        )
        payload = {
            'class_id': self.cls.id,
            'subject_id': self.subject.id,
            'date': '2026-11-15',
            'statuses': {str(outsider.id): 'present'},
        }
        resp = self.client.post(
            reverse('ai_api_attendance_save'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_save_denied_for_other_teacher(self):
        user2 = User.objects.create_user(username='t2', password='pw', role='teacher')
        TeacherProfile.objects.create(user=user2, full_name='Other')
        self.client.logout()
        self.client.login(username='t2', password='pw')
        payload = {
            'class_id': self.cls.id,
            'subject_id': self.subject.id,
            'date': '2026-11-15',
            'statuses': {str(self.s1.id): 'present'},
        }
        resp = self.client.post(
            reverse('ai_api_attendance_save'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 403)

    # ── photo ──

    def test_photo_404_when_missing(self):
        resp = self.client.get(reverse('ai_api_student_photo', args=[self.s1.id]))
        self.assertEqual(resp.status_code, 404)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_photo_served_for_valid_student(self):
        self.s1.profile_picture.save('p.gif', SimpleUploadedFile('p.gif', TINY_GIF))
        resp = self.client.get(reverse('ai_api_student_photo', args=[self.s1.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'image/gif')

    # ── pages ──

    def test_pages_render(self):
        for name in ('ai_attendance_session', 'ai_attendance_enroll'):
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 200, f'{name} failed: {resp.status_code}')

class AIPageSmokeTests(TestCase):
    """Render smoke tests for AI attendance pages and their static assets."""

    def setUp(self):
        self.school = School.objects.create(name='Smoke School')
        self.user = User.objects.create_user(
            username='tsmoke', password='pw', role='teacher', school=self.school
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.user, full_name='Smoke Teacher', school=self.school
        )
        self.cls = Class.objects.create(
            name='6', section='B', academic_year='2024-2025',
            school=self.school, class_teacher=self.teacher,
        )
        self.subject = Subject.objects.create(name='Sci', code='S1', school=self.school)
        TeacherSubjectAssignment.objects.create(
            teacher=self.teacher, subject=self.subject,
            assigned_class=self.cls, academic_year='2024-2025',
        )
        self.client.login(username='tsmoke', password='pw')

    def test_ai_pages_include_pipeline_scripts(self):
        cases = (
            ('ai_attendance_session', 'aiattendance/ai_session.html', 'ai/js/session.js'),
            ('ai_attendance_enroll', 'aiattendance/enroll.html', 'ai/js/enroll.js'),
        )
        for name, template, script in cases:
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 200, f'{name} -> {resp.status_code}')
            self.assertTemplateUsed(resp, template)
            self.assertContains(resp, script)
            self.assertContains(resp, 'ai/js/models.js')
            self.assertContains(resp, 'ai/js/ort.wasm.min.js')
            self.assertContains(resp, 'ai/js/arcface.js')

    def test_dashboard_links_to_ai_pages(self):
        resp = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse('ai_attendance_session'))
        self.assertContains(resp, reverse('ai_attendance_enroll'))
        self.assertContains(resp, 'AI Attendance')
        self.assertContains(resp, 'Face Enrollment')

    def test_ai_static_assets_exist(self):
        from django.contrib.staticfiles import finders

        assets = [
            'ai/js/ort.wasm.min.js',
            'ai/js/ort-wasm-simd-threaded.wasm',
            'ai/js/ort-wasm-simd-threaded.mjs',
            'ai/js/yunet.js',
            'ai/js/minifasnet.js',
            'ai/js/arcface.js',
            'ai/js/bytetrack.js',
            'ai/js/models.js',
            'ai/js/pipeline.js',
            'ai/js/session.js',
            'ai/js/enroll.js',
            'ai/models/yunet_2023mar.onnx',
            'ai/models/minifasnet_v2.onnx',
            'ai/models/arcface_mbf.onnx',
        ]
        for asset in assets:
            self.assertIsNotNone(finders.find(asset), f'missing static asset: {asset}')

    def test_ai_pages_require_login(self):
        self.client.logout()
        for name in ('ai_attendance_session', 'ai_attendance_enroll'):
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302)
            self.assertIn('login', resp['Location'].lower())
