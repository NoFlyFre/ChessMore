from django.shortcuts import render
from .models import Game
from django.http import HttpResponse

def classic_chess(request, room_number, name):
    games = Game.objects.filter(room_id=room_number)
    game = games.first()
    order = 1
    if game == None: #creazione del gioco nella tabella nel caso il room_number non corrisponda a nessuna entry della tabella
        game = Game()
        game.room_id = room_number
        game.player1 = name
        game.save()

    elif game.player1 != name and game.player2 == "Placeholder": #inserimento del giocatore 2 nel caso un nuovo giocatore acceda alla
        game.player2 = name                             #stanza mentre il giocatore 2 non è ancora stato definito
        order = 2
        game.save()

    elif game.player2 == name: #condizione necessaria per settare il giusto orientamento della tabella per il giocatore 2
        order = 2              #se riaccede una seconda volta alla partita
    
    elif name not in (game.player1, game.player2): #condizione per impedire che più di due giocatori si colleghino
        return HttpResponse("Ci sono già due giocatori che stanno giocando in questa stanza")
    
    ctx = {"title" : "Classic chess", "order": order, "room_number": room_number}
    return render(request, template_name="chessengine/classic_chess.html", context=ctx)
