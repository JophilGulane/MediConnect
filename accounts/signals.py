import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, PatientProfile, DoctorProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a profile when a new user is saved."""
    if created:
        if instance.role == 'patient':
            PatientProfile.objects.get_or_create(user=instance)
        elif instance.role == 'doctor':
            # Use a UUID placeholder so the unique constraint is never violated
            DoctorProfile.objects.get_or_create(
                user=instance,
                defaults={'license_number': f'PENDING-{uuid.uuid4().hex[:12].upper()}'}
            )
