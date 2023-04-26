from django.shortcuts import render

def classic_chess(request, room_number):
    ctx = {"title" : "Classic chess",}
    return render(request, template_name="chessengine/classic_chess.html", context=ctx)
