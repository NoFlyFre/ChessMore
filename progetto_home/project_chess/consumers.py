from channels.generic.websocket import AsyncWebsocketConsumer
import json
from multiplayer_chess.models import Game, Profile
from django.db .models import Max
from asgiref.sync import sync_to_async
from . import game_logic
import asyncio

class Lobby(AsyncWebsocketConsumer):

    lock = asyncio.Lock()

    connected_users = []
    
    firstConnection = {
        'classic': False,
        'atomic': False,
        'antichess': False,
        'kingofthehill': False,
        'threecheck': False,
        'horde': False,
        'racingkings': False
    }

    lastConnection = {
        'classic': False,
        'atomic': False,
        'antichess': False,
        'kingofthehill': False,
        'threecheck': False,
        'horde': False,
        'racingkings': False
    }

    def return_usernames(self):
        usernames = []
        for user in self.connected_users:
            usernames.append(user[0].username)
        return usernames
    
    def my_sync_crea_partita(self, user, mode_parameter, elo):
        max_id = Game.objects.aggregate(Max('room_id'))['room_id__max']
        game = Game()
        game.room_id = max_id + 1
        game.player1 = user
        game.mode = mode_parameter
        game.elo_partita = elo
        if mode_parameter == 'horde':
            game.fen = 'rnbqkbnr/pppppppp/8/1PP2PP1/PPPPPPPP/PPPPPPPP/PPPPPPPP/PPPPPPPP w kq - 0 1'
        elif mode_parameter == 'racingkings':
            game.fen = '8/8/8/8/8/8/krbnNBRK/qrbnNBRQ w - - 0 1'
        game.save()


    def my_sync_aggiungi_secondo_player(self, user, mode_parameter, elo):
    
        games = Game.objects.filter(player2__isnull=True, mode=mode_parameter, elo_partita = elo )
        game = games.first()
        game.player2 = user
        game.status = 'started'
        game.save()
        return game.room_id
    
    def my_sync_togli_partita(self, mode_parameter):
        games = Game.objects.filter(player1 = self.scope['user'], player2__isnull=True, mode=mode_parameter)
        if bool(games):
            game = games.first()
            game.delete()

    def my_sync_get_elo_mode(self, mode_parameter):
        user_profile = Profile.objects.get(user=self.scope['user'])
        if mode_parameter == 'classic':
            mode_elo = user_profile.elo_classic
        elif mode_parameter == 'antichess':
            mode_elo = user_profile.elo_antichess
        elif mode_parameter == 'atomic':
            mode_elo = user_profile.elo_atomic
        else: 
            mode_elo = 1000

        rounded_elo = round(mode_elo, -2)
        return rounded_elo

    
    async def connect(self):
        
        #dalla richiesta ricava l'utente e la modalità
        user = self.scope['user']
        self.mode = self.scope['url_route']['kwargs']['mode']

        #nome del gruppo
        self.room_group_name = 'canali_lobby_' + self.mode
        
        #aggiunge il canale al gruppo
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        self.rounded_elo = await sync_to_async(self.my_sync_get_elo_mode)(self.mode)

        #ricava gli utenti nella lobby in attesa per una determinata variante e con un determinato elo
        users_lobby_variant = [t[0] for t in self.connected_users if t[1] == self.mode and t[2] == self.rounded_elo]

        
        #se l'utente non è gia connesso per quella determinata variante imposta il
        #flag firstConnection a true
        if user not in users_lobby_variant:
            self.firstConnection[self.mode] = True
        else:
            self.firstConnection[self.mode] = False
        
        #aggiunge l'utente agli utenti in attesa per una determinata variante
        self.connected_users.append((user, self.mode, self.rounded_elo ))

        #riaggiorno la variabile (ora c'è un utente in più che è stato appena aggiunto)
        users_lobby_variant = [t[0] for t in self.connected_users if t[1] == self.mode and t[2] == self.rounded_elo]

        #ricava gli usernames degli utenti nella lobby in attesa per una determinata variante
        usernames_lobby_variant = []
        for user_lobby_variant in  users_lobby_variant:
            usernames_lobby_variant.append(user_lobby_variant.username)
        #rimuove le ripetizioni (ad. esempio lo stesso utente potrebbe avere due pagine aperte con la lobby)
        usernames_lobby_variant_no_repetition = list(set(usernames_lobby_variant))
        
        await self.accept()

        
        if len(usernames_lobby_variant_no_repetition) == 1:

            #evita che di creare infinite partite ogni volta che l'utente refresha la pagina
            if self.firstConnection[self.mode]:
                await sync_to_async(self.my_sync_crea_partita)(user, self.mode, self.rounded_elo)

            #greetings message
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": "Hello, everyone!",
                }
            )       

        if len(usernames_lobby_variant_no_repetition) == 2:
            #aggiunge il secondo giocatore alla partita
            room_id = await sync_to_async(self.my_sync_aggiungi_secondo_player)(user, self.mode, self.rounded_elo)
            #informa tutti coloro connessi al socket che la partita tra i due player sta per iniziare
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "match_found",
                    "message": f"{room_id}",
                    "mode": f"{self.mode}"
                }
            )

    async def disconnect(self, close_code):

        #dalla richiesta ricava l'utente e la modalità
        user = self.scope['user']
        self.mode = self.scope['url_route']['kwargs']['mode']
        self.rounded_elo = await sync_to_async(self.my_sync_get_elo_mode)(self.mode)

        #nome del gruppo
        self.room_group_name = 'canali_lobby_' + self.mode
        
        if self.connected_users.count((user, self.mode, self.rounded_elo )) == 1:
            self.lastConnection[self.mode] = True
        else:
            self.lastConnection[self.mode] = False

        self.connected_users.remove((user, self.mode, self.rounded_elo))

        if self.lastConnection[self.mode]:
            await sync_to_async(self.my_sync_togli_partita)(self.mode)

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def chat_message(self, event):
        message_type = event["type"]
        message = event["message"]
        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            "type": message_type,
            "message": message,
        }))

    async def match_found(self, event):
        message_type = event["type"]
        message = event["message"]
        mode = event["mode"]
        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            "type": message_type,
            "message" : message,
            "mode" : mode
        }))


#----------------------------------------------------------------------------------------------------------------

class WSConsumerChess(AsyncWebsocketConsumer):
    def obtain_players(self, room_id):
        games = Game.objects.filter(room_id=room_id)
        game = games.first()
        player1 = game.player1.username
        player2 = game.player2.username
        return {'player1':player1,'player2':player2,'game':game}

    #
    def my_sync_save_fen_and_turn(self, fen, turn):
        games = Game.objects.filter(pk=self.room_name)
        game = games.first()
        game.fen = fen
        game.turn = turn
        game.save()
    #

    def my_sync_retrive_fen(self):
        games = Game.objects.filter(pk=self.room_name)
        game = games.first()
        return game.fen

    def my_sync_save_winner(self, turn, quit_player):
        games = Game.objects.filter(pk=self.room_name)
        game = games.first()
        
        if game.winner is not None:
            return

        if (quit_player == game.player1.username) or (quit_player is None and turn == 'b'):
            loser = game.player1
            winner = game.player2
        elif (quit_player == game.player2.username) or (quit_player is None and turn == 'w'):
            loser = game.player2
            winner = game.player1
        else:
            return

        game.winner = winner
        if game.mode == 'classic':
            elo_field = 'elo_classic'
        elif game.mode == 'atomic':
            elo_field = 'elo_atomic'
        elif game.mode == 'antichess':
            elo_field = 'elo_antichess'

        profile_player1 = Profile.objects.get(user=winner)
        profile_player2 = Profile.objects.get(user=loser)

        setattr(profile_player1, elo_field, getattr(profile_player1, elo_field) + 7)
        setattr(profile_player2, elo_field, getattr(profile_player2, elo_field) - 7)
        
        profile_player1.save()
        profile_player2.save()

        game.status = 'finished'
        game.save()
        
    def my_sync_save_draw(self):
        games = Game.objects.filter(pk=self.room_name)
        game = games.first()
        game.status = 'finished'
        game.save()

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.variant = self.scope['url_route']['kwargs']['variant']
        self.room_group_name = 'game_' + self.room_name

        #
        fen = await sync_to_async(self.my_sync_retrive_fen)()
        game_logic.new_game(self.room_name, self.variant, fen)
        #


        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'connection_established',
                }
            )
        

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        players = await sync_to_async(self.obtain_players)(self.room_name)

        if(text_data_json['type'] == 'game_move'):
            san = game_logic.last_move(self.room_name, text_data_json['move'])
            result = game_logic.insert_move(self.room_name, text_data_json['move'])
            fen = game_logic.fen(self.room_name)
            status = game_logic.status(self.room_name)
            turn = game_logic.turn(self.room_name)

            if status in ["checkmate" , "var_loss"]:
                await sync_to_async(self.my_sync_save_winner)(('b' if turn == 'w' else 'w'), None)
            elif status == "stalemate" or status == "var_draw" or status == "insufficient":
                await sync_to_async(self.my_sync_save_draw)()
            
            await sync_to_async(self.my_sync_save_fen_and_turn)(fen, turn)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_move',
                    'fen': fen,
                    'status' : status,
                    'turn' : turn,
                    'last_move': san,
                    'result' : result,
                }
            )
        elif(text_data_json['type'] == 'messaggio'):
            message = text_data_json['message']
            username = text_data_json['username']
            await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )
        else:
            username = text_data_json['username']
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'abbandona',
                    'username': username
                }
            )
            if(players['player1'] == username):
                print("Ha quittato il player: " + players['player1'])
                await sync_to_async(self.my_sync_save_winner)('b', players['player1'])
            else:
                print("Ha quittato il player: " + players['player2'])
                await sync_to_async(self.my_sync_save_winner)('w', players['player2'])


    async def game_move(self, event):

        fen = event['fen']
        status = event['status']
        turn = event['turn']
        last_move = event['last_move']
        result = event['result']


        await self.send(text_data=json.dumps({
            'fen': fen,
            'status' : status,
            'turn' : turn,
            'last_move' : last_move,
            'result' : result,
            'type': 'game_move'
        }))


    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'type': 'messaggio'
        }))

    async def abbandona(self, event):
        username = event['username']
        await self.send(text_data=json.dumps({
            'username': username,
            'type': 'abbandona'
        }))
    async def connection_established(self, event):
        message_type = event["type"]
        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            "type": message_type,
            "message": "connessione al socket avvenuta con successo",
        }))
        