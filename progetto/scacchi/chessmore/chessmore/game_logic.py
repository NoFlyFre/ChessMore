import chess

games = {}
def new_game(id):
    games[id] = chess.Board()

def insert_move(id, move):
    try:
        games[id].push_uci(move)
        return "success"
    except ValueError:
        return "error"
    
def fen(id):
    return games[id].fen()
    
def status(id):
    if games[id].is_checkmate():
        return "checkmate"
    elif games[id].is_stalemate():
        return "stalemate"
    elif games[id].is_insufficient_material():
        return "insufficient"

def turn(id):
    if games[id].turn:
        return "w"
    else:
        return "b"

def last_move(id, move):
    try:
        return games[id].san(chess.Move.from_uci(move))
    except:
        return ""