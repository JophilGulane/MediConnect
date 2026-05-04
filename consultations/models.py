from django.db import models
from accounts.models import User


class Consultation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_consultations')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_consultations')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    symptoms_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    prescription_ready = models.BooleanField(default=False)

    def __str__(self):
        return f"Consultation #{self.pk} — {self.patient} with Dr. {self.doctor}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consultation'
        verbose_name_plural = 'Consultations'


class Message(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
    ]

    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField()  # text content or image URL
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message #{self.pk} by {self.sender} in Consultation #{self.consultation_id}"

    class Meta:
        ordering = ['sent_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'


class ConsultationImage(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='images')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_images')
    image = models.ImageField(upload_to='consultation_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Consultation #{self.consultation_id}"

    class Meta:
        ordering = ['uploaded_at']
        verbose_name = 'Consultation Image'
        verbose_name_plural = 'Consultation Images'
