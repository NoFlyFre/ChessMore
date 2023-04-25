from django.urls import path
from .views import *

app_name = "chessengine"

urlpatterns = [
    path("classic_chess/<int:room_number>/", classic_chess, name="classic_chess")
]