from django.shortcuts import render
from .chesslogic import *

def classic_chess(request, room_number):
    create_game(room_number)
    ctx = {"title" : "Classic chess",}
    return render(request, template_name="chessengine/classic_chess.html", context=ctx)
