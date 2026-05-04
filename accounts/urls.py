from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/patient/', views.PatientRegistrationView.as_view(), name='register_patient'),
    path('register/doctor/', views.DoctorRegistrationView.as_view(), name='register_doctor'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('doctor/pending/', views.doctor_pending_view, name='doctor_pending'),
]
