from channels.generic.websocket import AsyncWebsocketConsumer
import json

class WSConsumerChess(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_' + self.room_name

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
        move = text_data_json['move']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_move',
                'move': move,
                'sender_channel_name': self.channel_name,
            }
        )

    async def game_move(self, event):
        move = event['move']

        if self.channel_name != event['sender_channel_name']:
            await self.send(text_data=json.dumps({
                'move': move,
            }))
