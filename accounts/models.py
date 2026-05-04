from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def is_patient(self):
        return self.role == 'patient'

    def is_doctor(self):
        return self.role == 'doctor'

    def is_admin_user(self):
        return self.role == 'admin'

    def get_initials(self):
        parts = self.get_full_name().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        elif parts:
            return parts[0][:2].upper()
        return self.username[:2].upper()

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    class Meta:
        ordering = ['username']
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class PatientProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not', 'Prefer not to say'),
    ]
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A−', 'A−'),
        ('B+', 'B+'), ('B−', 'B−'),
        ('AB+', 'AB+'), ('AB−', 'AB−'),
        ('O+', 'O+'), ('O−', 'O−'),
        ('unknown', 'Unknown'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patientprofile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, default='unknown')
    allergies = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"PatientProfile — {self.user}"

    class Meta:
        verbose_name = 'Patient Profile'
        verbose_name_plural = 'Patient Profiles'


class DoctorProfile(models.Model):
    AVAILABILITY_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('busy', 'Busy'),
    ]
    SPECIALTY_CHOICES = [
        ('general', 'General Practice'),
        ('cardiology', 'Cardiology'),
        ('dermatology', 'Dermatology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('psychiatry', 'Psychiatry'),
        ('ophthalmology', 'Ophthalmology'),
        ('gynecology', 'Gynecology'),
        ('oncology', 'Oncology'),
        ('urology', 'Urology'),
        ('endocrinology', 'Endocrinology'),
        ('gastroenterology', 'Gastroenterology'),
        ('pulmonology', 'Pulmonology'),
        ('rheumatology', 'Rheumatology'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctorprofile')
    specialty = models.CharField(max_length=50, choices=SPECIALTY_CHOICES, default='general')
    license_number = models.CharField(max_length=50, unique=True)
    bio = models.TextField(blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    availability_status = models.CharField(
        max_length=10, choices=AVAILABILITY_CHOICES, default='offline'
    )
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} — {self.get_specialty_display()}"

    class Meta:
        ordering = ['-rating', 'user__last_name']
        verbose_name = 'Doctor Profile'
        verbose_name_plural = 'Doctor Profiles'
