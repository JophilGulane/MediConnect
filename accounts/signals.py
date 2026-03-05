from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, PatientProfile, DoctorProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'patient':
            PatientProfile.objects.get_or_create(user=instance)
        elif instance.role == 'doctor':
            DoctorProfile.objects.get_or_create(
                user=instance,
                defaults={'license_number': f'PENDING-{instance.pk}'}
            )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if instance.role == 'patient':
        if hasattr(instance, 'patientprofile'):
            instance.patientprofile.save()
    elif instance.role == 'doctor':
        if hasattr(instance, 'doctorprofile'):
            instance.doctorprofile.save()
