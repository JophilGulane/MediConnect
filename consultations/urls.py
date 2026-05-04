from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    path('<int:pk>/room/', views.consultation_room, name='room'),
    path('<int:pk>/messages/', views.fetch_messages, name='fetch_messages'),
    path('<int:pk>/upload-image/', views.upload_image, name='upload_image'),
    path('<int:pk>/end/', views.end_consultation, name='end'),
]
