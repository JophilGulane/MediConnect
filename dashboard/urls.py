from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('patient/', views.patient_home, name='patient_home'),
    path('patient/doctors/', views.browse_doctors, name='browse_doctors'),
    path('patient/consult/new/', views.new_consultation, name='new_consultation'),
    path('patient/history/', views.patient_history, name='patient_history'),
    path('doctor/', views.doctor_home, name='doctor_home'),
    path('doctor/status/', views.doctor_status_toggle, name='doctor_status'),
    path('doctor/accept/', views.doctor_accept, name='doctor_accept'),
    path('doctor/history/', views.doctor_history, name='doctor_history'),
    path('admin/', views.admin_home, name='admin_home'),
    path('admin/doctors/', views.admin_doctors, name='admin_doctors'),
    path('admin/doctors/<int:doctor_id>/verify/', views.admin_verify_doctor, name='admin_verify_doctor'),
    path('admin/doctors/<int:doctor_id>/reject/', views.admin_reject_doctor, name='admin_reject_doctor'),
    path('admin/users/', views.admin_users, name='admin_users'),
]
