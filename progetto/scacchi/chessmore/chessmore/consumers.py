from channels.generic.websocket import AsyncWebsocketConsumer
import json
from . import game_logic

class WSConsumerChess(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_' + self.room_name
        game_logic.new_game(self.room_name)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
    
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
                    #'sender_channel_name': self.channel_name,
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