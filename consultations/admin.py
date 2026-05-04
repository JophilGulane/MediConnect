from django.contrib import admin
from .models import Consultation, Message, ConsultationImage


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['pk', 'patient', 'doctor', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['patient__username', 'doctor__username']
    ordering = ['-created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['pk', 'consultation', 'sender', 'message_type', 'sent_at']
    list_filter = ['message_type']


@admin.register(ConsultationImage)
class ConsultationImageAdmin(admin.ModelAdmin):
    list_display = ['pk', 'consultation', 'uploaded_by', 'uploaded_at']
