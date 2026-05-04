from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.home, name='home'),
    path('dashboard/patient/', views.patient_home, name='patient_home'),
    path('dashboard/patient/doctors/', views.browse_doctors, name='browse_doctors'),
    path('dashboard/patient/consult/new/', views.new_consultation, name='new_consultation'),
    path('dashboard/patient/history/', views.patient_history, name='patient_history'),
    path('dashboard/doctor/', views.doctor_home, name='doctor_home'),
    path('dashboard/doctor/status/', views.doctor_status_toggle, name='doctor_status'),
    path('dashboard/doctor/accept/', views.doctor_accept, name='doctor_accept'),
    path('dashboard/doctor/history/', views.doctor_history, name='doctor_history'),
    path('dashboard/admin/', views.admin_home, name='admin_home'),
    path('dashboard/admin/doctors/', views.admin_doctors, name='admin_doctors'),
    path('dashboard/admin/doctors/<int:doctor_id>/verify/', views.admin_verify_doctor, name='admin_verify_doctor'),
    path('dashboard/admin/doctors/<int:doctor_id>/reject/', views.admin_reject_doctor, name='admin_reject_doctor'),
    path('dashboard/admin/users/', views.admin_users, name='admin_users'),
]
