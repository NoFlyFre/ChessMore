import chess

games = {}

def create_game(ID):
    games[ID] = chess.Board()

def is_valid_move(ID, move):
    return games[ID].is_valid(move)

def push_move(ID, move):
    games[ID].push_uci(move)

def has_ended(ID):
    return games[ID].is_game_over()