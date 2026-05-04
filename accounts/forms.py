from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, PatientProfile, DoctorProfile


class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, label='First Name')
    last_name = forms.CharField(max_length=50, required=True, label='Last Name')
    email = forms.EmailField(required=True, label='Email Address')
    phone = forms.CharField(max_length=20, required=False, label='Phone Number')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'patient'
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user


class DoctorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, label='First Name')
    last_name = forms.CharField(max_length=50, required=True, label='Last Name')
    email = forms.EmailField(required=True, label='Email Address')
    phone = forms.CharField(max_length=20, required=False, label='Phone Number')
    specialty = forms.ChoiceField(choices=DoctorProfile.SPECIALTY_CHOICES, required=True, label='Specialty')
    license_number = forms.CharField(max_length=50, required=True, label='Medical License Number')
    years_of_experience = forms.IntegerField(min_value=0, max_value=60, required=True, label='Years of Experience')
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label='Short Bio'
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            'first_name', 'last_name', 'username', 'email', 'phone',
            'specialty', 'license_number', 'years_of_experience', 'bio',
            'password1', 'password2'
        ]

    def clean_license_number(self):
        license_number = self.cleaned_data.get('license_number', '').strip()
        if DoctorProfile.objects.filter(license_number=license_number).exists():
            raise forms.ValidationError(
                'A doctor with this license number is already registered.'
            )
        return license_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'doctor'
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        user.is_active = True  # Account is active but doctor needs admin verification
        if commit:
            user.save()
            profile = user.doctorprofile
            profile.specialty = self.cleaned_data['specialty']
            profile.license_number = self.cleaned_data['license_number']
            profile.years_of_experience = self.cleaned_data['years_of_experience']
            profile.bio = self.cleaned_data.get('bio', '')
            profile.is_verified = False
            profile.save()
        return user


class PatientProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)
    phone = forms.CharField(max_length=20, required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = PatientProfile
        fields = ['date_of_birth', 'gender', 'blood_type', 'allergies', 'medical_history', 'emergency_contact']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'allergies': forms.Textarea(attrs={'rows': 3}),
            'medical_history': forms.Textarea(attrs={'rows': 4}),
        }


class DoctorProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = DoctorProfile
        fields = ['specialty', 'bio', 'years_of_experience']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
