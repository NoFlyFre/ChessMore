from django.urls import path
from .views import *

app_name = "chessengine"

urlpatterns = [
    path("<str:variant>/<str:room_number>/<str:name>/", chess_game, name="chess_game")
]