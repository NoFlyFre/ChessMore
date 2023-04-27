from django.urls import path
from .consumers import WSConsumerChess

ws_urlpatterns = [
    path("ws/chessws/<str:room_name>/", WSConsumerChess.as_asgi()),
]