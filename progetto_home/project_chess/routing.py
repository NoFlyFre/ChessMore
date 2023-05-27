from django.urls import path
from .consumers import Lobby, WSConsumerChess

ws_urlpatterns = [
    path("ws/lobbyws/<str:mode>/", Lobby.as_asgi()),
    #--------------------------------------------------------------------
    path("ws/chessws/<str:room_name>/<str:variant>/", WSConsumerChess.as_asgi()),
]