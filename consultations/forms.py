from django import forms
from .models import Consultation


class NewConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['doctor', 'symptoms_description']
        widgets = {
            'symptoms_description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe your symptoms in detail…'}),
        }
        labels = {
            'doctor': 'Select a Doctor',
            'symptoms_description': 'Describe Your Symptoms',
        }
