from django.urls import path
from .consumers import *

ws_urlpatterns = [
    path("ws/lobbyws/", Lobby.as_asgi()),
    #--------------------------------------------------------------------
    path("ws/chessws/<str:room_name>/", WSConsumerChess.as_asgi()),
]