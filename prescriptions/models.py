from django.db import models
from accounts.models import User
from consultations.models import Consultation


class Prescription(models.Model):
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='prescription')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issued_prescriptions')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_prescriptions')
    medicines = models.JSONField(default=list)  # list of {name, dosage, frequency, duration}
    notes = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='prescriptions/', blank=True, null=True)

    def __str__(self):
        return f"Prescription #{self.pk} for {self.patient} by Dr. {self.doctor}"

    class Meta:
        ordering = ['-issued_at']
        verbose_name = 'Prescription'
        verbose_name_plural = 'Prescriptions'
