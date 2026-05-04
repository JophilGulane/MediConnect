from django import forms
from .models import Prescription


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['notes', 'instructions']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional clinical notes…'}),
            'instructions': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Patient instructions (e.g. take with food, avoid alcohol)…'}),
        }
        labels = {
            'notes': 'Clinical Notes',
            'instructions': 'Patient Instructions',
        }
