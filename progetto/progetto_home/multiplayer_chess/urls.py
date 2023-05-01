from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name = 'multiplayer_chess'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.loginView, name='login'),
    path('logout/', views.logoutView, name='logout'),
    path('register/', views.registerView, name='register'),
    path('home/', views.home, name='home'),
    path('edit/', views.edit, name='edit'),
    path('password-change/', views.my_password_change_view, name='password_change'),
    path("lobby/", views.lobby, name="lobby"),
    #----------------------------------------------------------------------------------------------------
    path("classic_chess/<str:room_number>/", views.classic_chess, name="classic_chess"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


