from django.urls import path
from .consumers import WSConsumerChess

ws_urlpatterns = [
    path("ws/chessws/<str:room_name>/<str:variant>/", WSConsumerChess.as_asgi()),
]