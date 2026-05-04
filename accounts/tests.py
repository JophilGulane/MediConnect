"""
Tests for the accounts app — models, views, forms, decorators.
"""
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, PatientProfile, DoctorProfile


class UserModelTest(TestCase):
    """Tests for the custom User model."""

    def test_create_patient(self):
        user = User.objects.create_user(
            username='patient1', password='testpass123',
            first_name='John', last_name='Doe', role='patient'
        )
        self.assertTrue(user.is_patient())
        self.assertFalse(user.is_doctor())
        self.assertFalse(user.is_admin_user())

    def test_create_doctor(self):
        user = User.objects.create_user(
            username='doctor1', password='testpass123',
            first_name='Jane', last_name='Smith', role='doctor'
        )
        self.assertTrue(user.is_doctor())
        self.assertFalse(user.is_patient())

    def test_create_admin(self):
        user = User.objects.create_user(
            username='admin1', password='testpass123', role='admin'
        )
        self.assertTrue(user.is_admin_user())

    def test_get_initials_full(self):
        user = User.objects.create_user(
            username='test', password='p', first_name='Maria', last_name='Reyes'
        )
        self.assertEqual(user.get_initials(), 'MR')

    def test_get_initials_first_only(self):
        user = User.objects.create_user(
            username='test2', password='p', first_name='Maria'
        )
        self.assertEqual(user.get_initials(), 'MA')

    def test_get_initials_fallback(self):
        user = User.objects.create_user(username='foobar', password='p')
        self.assertEqual(user.get_initials(), 'FO')


class SignalTest(TestCase):
    """Signals should auto-create profiles."""

    def test_patient_profile_created(self):
        user = User.objects.create_user(
            username='p1', password='pw', role='patient'
        )
        self.assertTrue(hasattr(user, 'patientprofile'))
        self.assertIsInstance(user.patientprofile, PatientProfile)

    def test_doctor_profile_created(self):
        user = User.objects.create_user(
            username='d1', password='pw', role='doctor'
        )
        self.assertTrue(hasattr(user, 'doctorprofile'))
        self.assertIsInstance(user.doctorprofile, DoctorProfile)
        self.assertFalse(user.doctorprofile.is_verified)


class RegistrationViewTest(TestCase):
    """Test patient and doctor registration flows."""

    def setUp(self):
        self.client = Client()

    def test_patient_register_get(self):
        resp = self.client.get(reverse('accounts:register_patient'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Create Patient Account')

    def test_patient_register_post(self):
        resp = self.client.post(reverse('accounts:register_patient'), {
            'username': 'newpatient',
            'first_name': 'New',
            'last_name': 'Patient',
            'email': 'new@test.com',
            'password1': 'Str0ngPass!23',
            'password2': 'Str0ngPass!23',
        })
        self.assertEqual(resp.status_code, 302)  # Redirect after success
        user = User.objects.get(username='newpatient')
        self.assertEqual(user.role, 'patient')
        self.assertTrue(hasattr(user, 'patientprofile'))

    def test_doctor_register_get(self):
        resp = self.client.get(reverse('accounts:register_doctor'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Create Doctor Account')

    def test_doctor_register_post(self):
        resp = self.client.post(reverse('accounts:register_doctor'), {
            'username': 'newdoctor',
            'first_name': 'Doc',
            'last_name': 'Tor',
            'email': 'doc@test.com',
            'password1': 'Str0ngPass!23',
            'password2': 'Str0ngPass!23',
            'specialty': 'general',
            'license_number': 'LIC-12345',
            'years_of_experience': 5,
        })
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(username='newdoctor')
        self.assertEqual(user.role, 'doctor')
        self.assertFalse(user.doctorprofile.is_verified)


class LoginViewTest(TestCase):
    """Test login behavior."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', password='Str0ngPass!23',
            first_name='Test', last_name='User', role='patient'
        )

    def test_login_page_loads(self):
        resp = self.client.get(reverse('accounts:login'))
        self.assertEqual(resp.status_code, 200)

    def test_login_success(self):
        resp = self.client.post(reverse('accounts:login'), {
            'username': 'loginuser',
            'password': 'Str0ngPass!23',
        })
        self.assertEqual(resp.status_code, 302)


class DecoratorTest(TestCase):
    """Test role-based access decorators."""

    def setUp(self):
        self.patient = User.objects.create_user(
            username='p', password='pw', role='patient', first_name='P', last_name='U'
        )
        self.doctor = User.objects.create_user(
            username='d', password='pw', role='doctor', first_name='D', last_name='U'
        )
        self.doctor.doctorprofile.is_verified = True
        self.doctor.doctorprofile.save()
        self.admin = User.objects.create_user(
            username='a', password='pw', role='admin', first_name='A', last_name='U'
        )

    def test_patient_cannot_access_doctor_home(self):
        self.client.login(username='p', password='pw')
        resp = self.client.get(reverse('dashboard:doctor_home'))
        self.assertEqual(resp.status_code, 403)

    def test_doctor_cannot_access_admin_home(self):
        self.client.login(username='d', password='pw')
        resp = self.client.get(reverse('dashboard:admin_home'))
        self.assertEqual(resp.status_code, 403)

    def test_patient_can_access_own_dashboard(self):
        self.client.login(username='p', password='pw')
        resp = self.client.get(reverse('dashboard:patient_home'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_can_access_admin_home(self):
        self.client.login(username='a', password='pw')
        resp = self.client.get(reverse('dashboard:admin_home'))
        self.assertEqual(resp.status_code, 200)
