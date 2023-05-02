from channels.generic.websocket import AsyncWebsocketConsumer
import json
from multiplayer_chess.models import Game
from django.db.models import Max
from asgiref.sync import sync_to_async

class Lobby(AsyncWebsocketConsumer):


    connected_users = []
    channel_counter = 0
    firstConnection = False

    def return_usernames(self):
        usernames = []
        for user in self.connected_users:
            usernames.append(user.username)
        return usernames
    
    def my_sync_crea_partita(self, user):
        max_id = Game.objects.aggregate(Max('room_id'))['room_id__max']
        game = Game()
        game.room_id = max_id + 1
        game.player1 = user
        game.save()


    def my_sync_aggiungi_secondo_player(self, user):
        games = Game.objects.filter(player2__isnull=True)
        game = games.first()
        game.player2 = user
        game.save()
        return game.room_id
    
    def my_sync_togli_partita(self):
        games = Game.objects.filter(player2__isnull=True)
        if bool(games):
            print("debugging")
            print(games)
            game = games.first()
            game.delete()
    

    async def connect(self):

        user = self.scope['user']

        await self.channel_layer.group_add(
            "canali_lobby",
            self.channel_name
        )

        if user not in self.connected_users:
            Lobby.channel_counter += 1
            self.firstConnection = True
        else:
            self.firstConnection = False
        
        self.connected_users.append(user)
        usernames = self.return_usernames()

        await self.accept()

        if Lobby.channel_counter == 1:

            if self.firstConnection:
                await sync_to_async(self.my_sync_crea_partita)(user)

            await self.channel_layer.group_send(
                "canali_lobby",
                {
                    "type": "chat_message",
                    "message": f"Hello, everyone! {usernames}",
                }
            )       

        if Lobby.channel_counter == 2:

            room_id = await sync_to_async(self.my_sync_aggiungi_secondo_player)(user)
            await self.channel_layer.group_send(
                "canali_lobby",
                {
                    "type": "match_found",
                    "message": f"{room_id}",
                }
            )
    

        print(Lobby.channel_counter)


    async def disconnect(self, close_code):
        # Remove the user from the list of connected users
        user = self.scope['user']
    
        if self.connected_users.count(user) == 1:
            Lobby.channel_counter -= 1
            self.lastConnection = True
        else:
            self.lastConnection = False

        self.connected_users.remove(self.scope['user'])

        if self.lastConnection:
            await sync_to_async(self.my_sync_togli_partita)()

        await self.channel_layer.group_discard(
            "canali_lobby",
            self.channel_name
        )

        print(Lobby.channel_counter)

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
        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            "type": type,
            "message" : message
        }))


#----------------------------------------------------------------------------------------------------------------

class WSConsumerChess(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_' + self.room_name

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
            move = text_data_json['move']
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_move',
                    'move': move,
                    'sender_channel_name': self.channel_name,
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
        move = event['move']

        if self.channel_name != event['sender_channel_name']:
            await self.send(text_data=json.dumps({
                'move': move,
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

