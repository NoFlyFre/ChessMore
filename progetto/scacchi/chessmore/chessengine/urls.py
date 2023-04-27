from django.urls import path
from .views import *

app_name = "chessengine"

urlpatterns = [
    path("classic_chess/<str:room_number>/<str:name>/", classic_chess, name="classic_chess")
]