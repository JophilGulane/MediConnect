"""
Tests for the prescriptions app — models, views, PDF generation.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from consultations.models import Consultation
from prescriptions.models import Prescription


class PrescriptionModelTest(TestCase):
    """Test Prescription model."""

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
            symptoms_description='Test', status='completed'
        )

    def test_create_prescription(self):
        rx = Prescription.objects.create(
            consultation=self.consultation,
            doctor=self.doctor,
            patient=self.patient,
            medicines=[{'name': 'Amoxicillin', 'dosage': '500mg', 'frequency': '3x/day', 'duration': '7 days'}],
            notes='Bacterial infection',
            instructions='Take after meals',
        )
        self.assertEqual(rx.doctor, self.doctor)
        self.assertEqual(len(rx.medicines), 1)
        self.assertEqual(rx.medicines[0]['name'], 'Amoxicillin')


class PrescriptionViewTest(TestCase):
    """Test prescription views and access control."""

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
            symptoms_description='Test', status='completed'
        )

    def test_create_prescription_page_loads(self):
        self.client.login(username='d', password='pw')
        resp = self.client.get(
            reverse('prescriptions:create', args=[self.consultation.pk])
        )
        self.assertEqual(resp.status_code, 200)

    def test_create_prescription_post(self):
        self.client.login(username='d', password='pw')
        medicines = json.dumps([
            {'name': 'Ibuprofen', 'dosage': '400mg', 'frequency': '2x/day', 'duration': '5 days'}
        ])
        resp = self.client.post(
            reverse('prescriptions:create', args=[self.consultation.pk]),
            {
                'medicines_json': medicines,
                'notes': 'Mild inflammation',
                'instructions': 'Take with food',
            }
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Prescription.objects.count(), 1)
        rx = Prescription.objects.first()
        self.assertEqual(rx.patient, self.patient)
        self.assertTrue(rx.pdf_file)  # PDF should have been generated

    def test_patient_cannot_create_prescription(self):
        self.client.login(username='p', password='pw')
        resp = self.client.get(
            reverse('prescriptions:create', args=[self.consultation.pk])
        )
        self.assertEqual(resp.status_code, 403)

    def test_prescription_detail_accessible(self):
        rx = Prescription.objects.create(
            consultation=self.consultation,
            doctor=self.doctor,
            patient=self.patient,
            medicines=[{'name': 'Test', 'dosage': '100mg', 'frequency': '1x', 'duration': '3d'}],
        )
        self.client.login(username='p', password='pw')
        resp = self.client.get(reverse('prescriptions:detail', args=[rx.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Digital Prescription')

    def test_prescription_detail_blocked_for_unrelated_user(self):
        rx = Prescription.objects.create(
            consultation=self.consultation,
            doctor=self.doctor,
            patient=self.patient,
            medicines=[],
        )
        other = User.objects.create_user(
            username='other', password='pw', role='patient', first_name='X', last_name='Y'
        )
        self.client.login(username='other', password='pw')
        resp = self.client.get(reverse('prescriptions:detail', args=[rx.pk]))
        self.assertEqual(resp.status_code, 403)
