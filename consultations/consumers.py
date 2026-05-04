import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ConsultationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        user = self.scope['user']

        if not user.is_authenticated:
            await self.close(code=4001)
            return

        is_participant = await self.check_participant(user, self.consultation_id)
        if not is_participant:
            await self.close(code=4003)
            return

        self.room_group_name = f'consultation_{self.consultation_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        event_type = data.get('type')

        if event_type == 'chat_message':
            content = data.get('content', '').strip()
            if not content:
                return
            message = await self.save_message(data)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat_message',
                'message_id': message.pk,
                'content': content,
                'sender': data.get('sender', ''),
                'sender_id': data.get('sender_id'),
                'sent_at': message.sent_at.strftime('%H:%M'),
                'message_type': 'text',
            })

        elif event_type == 'image_message':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat_message',
                'content': data.get('image_url', ''),
                'sender': data.get('sender', ''),
                'sender_id': data.get('sender_id'),
                'sent_at': data.get('sent_at', ''),
                'message_type': 'image',
            })

        elif event_type == 'typing':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'typing_indicator',
                'sender': data.get('sender', ''),
                'sender_id': data.get('sender_id'),
                'is_typing': data.get('is_typing', False),
            })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, data):
        from consultations.models import Message, Consultation
        from accounts.models import User as UserModel
        consultation = Consultation.objects.get(pk=self.consultation_id)
        sender = UserModel.objects.get(pk=data['sender_id'])
        return Message.objects.create(
            consultation=consultation,
            sender=sender,
            message_type='text',
            content=data['content']
        )

    @database_sync_to_async
    def check_participant(self, user, consultation_id):
        from consultations.models import Consultation
        try:
            c = Consultation.objects.get(pk=consultation_id)
            return user.pk in [c.patient_id, c.doctor_id]
        except Consultation.DoesNotExist:
            return False
