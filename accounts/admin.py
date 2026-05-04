from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientProfile, DoctorProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('MediConnect', {'fields': ('role', 'phone', 'profile_picture')}),
    )


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'gender', 'blood_type', 'date_of_birth']
    search_fields = ['user__username', 'user__email']


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialty', 'license_number', 'is_verified', 'availability_status', 'rating']
    list_filter = ['is_verified', 'specialty', 'availability_status']
    list_editable = ['is_verified']
    actions = ['approve_doctors', 'reject_doctors']
    search_fields = ['user__username', 'user__email', 'license_number']

    def approve_doctors(self, request, queryset):
        updated = queryset.update(is_verified=True)
        for profile in queryset:
            profile.user.is_active = True
            profile.user.save()
        self.message_user(request, f'{updated} doctor(s) approved successfully.')
    approve_doctors.short_description = 'Approve selected doctors'

    def reject_doctors(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} doctor(s) rejected.')
    reject_doctors.short_description = 'Reject selected doctors'
