import json
from channels.generic.websocket import AsyncWebsocketConsumer

class OrderNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.outlet_id = self.scope['url_route']['kwargs']['outlet_id']
        self.room_group_name = f'outlet_{self.outlet_id}_orders'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from room group
    async def new_order_notification(self, event):
        message = event['message']
        order_data = event.get('order_data', {})

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_order',
            'message': message,
            'order_data': order_data
        }))
