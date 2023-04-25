from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='edit'),
    
    path('play/', views.giocapartita, name='giocapartita'),
    path('play/internazionali', views.gioca_internazionali, name='gioca_internazionali'),
    path('play/vinciperdi', views.gioca_vinciperdi, name='gioca_vinciperdi'),
    path('play/progressivi', views.gioca_progressivi, name='gioca_progressivi'),
    path('play/atomici', views.gioca_atomici, name='gioca_atomici'),


]