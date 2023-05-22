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
    path("lobby/<str:mode>/", views.lobby, name="lobby"),
    path("<str:variant>/<str:room_number>/", views.chess_game, name="chess_game"),
    path("<str:variant>/<str:room_number>/get_position/", views.get_position, name="get_position"),
    path('cronologia/', views.cronologia, name='cronologia'),
    path("tournament-list/", views.tournament_list, name='tournament_list'),
    path("tournament/view/<str:tour_id>/", views.tournament_details, name='tournament_details'),
    path("tournament/view/<str:tour_id>/sub", views.tournament_subscribe, name='tournament_subscribe'),
    path("tournament/view/<str:tour_id>/unsub", views.tournament_unsubscribe, name='tournament_unsubscribe')
    #----------------------------------------------------------------------------------------------------
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

