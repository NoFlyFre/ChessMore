from channels.generic.websocket import AsyncWebsocketConsumer
import json
from multiplayer_chess .models import Game
from django.db .models import Max
from asgiref.sync import sync_to_async
from . import game_logic

class Lobby(AsyncWebsocketConsumer):


    connected_users = []
    
    channel_counter = {
        'classic': 0,
        'atomic': 0,
    }

    firstConnection = {
        'classic': False,
        'atomic': False,
    }

    lastConnection = {
        'classic': False,
        'atomic': False,
    }

    def return_usernames(self):
        usernames = []
        for user in self.connected_users:
            usernames.append(user[0].username)
        return usernames
    
    def my_sync_crea_partita(self, user, mode_parameter):
        max_id = Game.objects.aggregate(Max('room_id'))['room_id__max']
        game = Game()
        game.room_id = max_id + 1
        game.player1 = user
        game.mode = mode_parameter
        game.save()


    def my_sync_aggiungi_secondo_player(self, user, mode_parameter):
        games = Game.objects.filter(player2__isnull=True, mode=mode_parameter)
        game = games.first()
        game.player2 = user
        game.save()
        return game.room_id
    
    def my_sync_togli_partita(self, mode_parameter):
        games = Game.objects.filter(player2__isnull=True, mode=mode_parameter)
        if bool(games):
            game = games.first()
            game.delete()
    

    async def connect(self):

        user = self.scope['user']
        self.mode = self.scope['url_route']['kwargs']['mode']
        self.room_group_name = 'canali_lobby_' + self.mode

        print(f'debugging: mode = {self.mode}')
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        users_right_now = [t[0] for t in self.connected_users if t[1] == self.mode]
        if user not in users_right_now:
            Lobby.channel_counter[self.mode] += 1
            self.firstConnection[self.mode] = True
        else:
            self.firstConnection[self.mode] = False
        
        self.connected_users.append((user, self.mode))
        usernames = self.return_usernames()

        await self.accept()

        if Lobby.channel_counter[self.mode] == 1:

            if self.firstConnection[self.mode]:
                await sync_to_async(self.my_sync_crea_partita)(user, self.mode)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": f"Hello, everyone! {usernames}",
                }
            )       

        print(Lobby.channel_counter [self.mode])

        if Lobby.channel_counter [self.mode] == 2:

            room_id = await sync_to_async(self.my_sync_aggiungi_secondo_player)(user, self.mode)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "match_found",
                    "message": f"{room_id}",
                    "mode": f"{self.mode}"
                }
            )
    


    async def disconnect(self, close_code):
        # Remove the user from the list of connected users
        user = self.scope['user']
        self.mode = self.scope['url_route']['kwargs']['mode']

        
        self.room_group_name = 'canali_lobby_' + self.mode
        
        if self.connected_users[0].count(user) == 1:
            Lobby.channel_counter [self.mode] -= 1
            self.lastConnection[self.mode] = True
        else:
            self.lastConnection[self.mode] = False

        self.connected_users.remove((self.scope['user'], self.mode))

        if self.lastConnection:
            await sync_to_async(self.my_sync_togli_partita)(self.mode)

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        print(Lobby.channel_counter[self.mode])

    async def chat_message(self, event):
        type = event["type"]
        message = event["message"]
        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            "type": type,
            "message": message,
        }))

    async def match_found(self, event):
        type = event["type"]
        message = event["message"]
        mode = event["mode"]
        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            "type": type,
            "message" : message,
            "mode" : mode
        }))


#----------------------------------------------------------------------------------------------------------------

class WSConsumerChess(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.variant = self.scope['url_route']['kwargs']['variant']
        self.room_group_name = 'game_' + self.room_name
        game_logic.new_game(self.room_name, self.variant)

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

        if(text_data_json['type'] == 'game_move'):

            san = game_logic.last_move(self.room_name, text_data_json['move'])
            result = game_logic.insert_move(self.room_name, text_data_json['move'])
            fen = game_logic.fen(self.room_name)
            status = game_logic.status(self.room_name)
            turn = game_logic.turn(self.room_name)

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
        else:
            message = text_data_json['message']
            username = text_data_json['username']
            #room = text_data_json['room']
            await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

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

    async def connection_established(self, event):
        type = event["type"]
        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            "type": type,
            "message": "connessione al socket avvenuta con successo",
        }))

