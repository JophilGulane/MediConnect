from django.contrib import admin
from .models import Prescription


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['pk', 'patient', 'doctor', 'issued_at', 'consultation']
    list_filter = ['issued_at']
    search_fields = ['patient__username', 'doctor__username']
    ordering = ['-issued_at']
