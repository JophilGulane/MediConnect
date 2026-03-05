from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    path('create/<int:consultation_pk>/', views.create_prescription, name='create'),
    path('<int:pk>/', views.prescription_detail, name='detail'),
    path('<int:pk>/download/', views.download_prescription, name='download'),
]
