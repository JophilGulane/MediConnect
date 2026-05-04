"""
Tests for the consultations app — models, views.
"""
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from consultations.models import Consultation, Message


class ConsultationModelTest(TestCase):
    """Tests for the Consultation model."""

    def setUp(self):
        self.patient = User.objects.create_user(
            username='p', password='pw', role='patient', first_name='Pat', last_name='Ient'
        )
        self.doctor = User.objects.create_user(
            username='d', password='pw', role='doctor', first_name='Doc', last_name='Tor'
        )
        self.doctor.doctorprofile.is_verified = True
        self.doctor.doctorprofile.save()

    def test_create_consultation(self):
        c = Consultation.objects.create(
            patient=self.patient, doctor=self.doctor,
            symptoms_description='Headache for 3 days', status='pending'
        )
        self.assertEqual(c.status, 'pending')
        self.assertEqual(str(c.patient), 'Pat Ient (patient)')

    def test_consultation_status_transitions(self):
        c = Consultation.objects.create(
            patient=self.patient, doctor=self.doctor,
            symptoms_description='Test', status='pending'
        )
        c.status = 'active'
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'active')

    def test_message_ordering(self):
        c = Consultation.objects.create(
            patient=self.patient, doctor=self.doctor,
            symptoms_description='Test', status='active'
        )
        m1 = Message.objects.create(consultation=c, sender=self.patient, content='Hello')
        m2 = Message.objects.create(consultation=c, sender=self.doctor, content='Hi there')
        msgs = list(c.messages.all())
        self.assertEqual(msgs[0], m1)
        self.assertEqual(msgs[1], m2)


class ConsultationViewTest(TestCase):
    """Test consultation views and access control."""

    def setUp(self):
        self.patient = User.objects.create_user(
            username='p', password='pw', role='patient', first_name='Pat', last_name='Ient'
        )
        self.doctor = User.objects.create_user(
            username='d', password='pw', role='doctor', first_name='Doc', last_name='Tor'
        )
        self.doctor.doctorprofile.is_verified = True
        self.doctor.doctorprofile.save()
        self.consultation = Consultation.objects.create(
            patient=self.patient, doctor=self.doctor,
            symptoms_description='Test symptoms', status='active'
        )

    def test_room_requires_login(self):
        resp = self.client.get(
            reverse('consultations:room', args=[self.consultation.pk])
        )
        self.assertEqual(resp.status_code, 302)  # Redirect to login

    def test_room_accessible_by_patient(self):
        self.client.login(username='p', password='pw')
        resp = self.client.get(
            reverse('consultations:room', args=[self.consultation.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_room_accessible_by_doctor(self):
        self.client.login(username='d', password='pw')
        resp = self.client.get(
            reverse('consultations:room', args=[self.consultation.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_room_blocked_for_unrelated_user(self):
        other = User.objects.create_user(
            username='other', password='pw', role='patient', first_name='X', last_name='Y'
        )
        self.client.login(username='other', password='pw')
        resp = self.client.get(
            reverse('consultations:room', args=[self.consultation.pk])
        )
        self.assertEqual(resp.status_code, 403)

    def test_fetch_messages_ajax(self):
        Message.objects.create(
            consultation=self.consultation, sender=self.patient, content='Hello'
        )
        self.client.login(username='p', password='pw')
        resp = self.client.get(
            reverse('consultations:fetch_messages', args=[self.consultation.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(len(data['messages']), 1)

    def test_end_consultation_by_doctor(self):
        self.client.login(username='d', password='pw')
        resp = self.client.post(
            reverse('consultations:end', args=[self.consultation.pk])
        )
        self.assertEqual(resp.status_code, 302)  # Redirect to create prescription
        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.status, 'completed')


class NewConsultationTest(TestCase):
    """Test creating a new consultation."""

    def setUp(self):
        self.patient = User.objects.create_user(
            username='p', password='pw', role='patient', first_name='Pat', last_name='Ient'
        )
        self.doctor = User.objects.create_user(
            username='d', password='pw', role='doctor', first_name='Doc', last_name='Tor'
        )
        self.doctor.doctorprofile.is_verified = True
        self.doctor.doctorprofile.availability_status = 'online'
        self.doctor.doctorprofile.save()

    def test_new_consultation_page(self):
        self.client.login(username='p', password='pw')
        resp = self.client.get(reverse('dashboard:new_consultation'))
        self.assertEqual(resp.status_code, 200)

    def test_submit_new_consultation(self):
        self.client.login(username='p', password='pw')
        resp = self.client.post(reverse('dashboard:new_consultation'), {
            'doctor': self.doctor.pk,
            'symptoms_description': 'I have a headache for 3 days.',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Consultation.objects.count(), 1)
        c = Consultation.objects.first()
        self.assertEqual(c.patient, self.patient)
        self.assertEqual(c.doctor, self.doctor)
        self.assertEqual(c.status, 'pending')
