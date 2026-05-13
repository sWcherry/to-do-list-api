import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import OnlineUser, UserActivity, RealtimeNotification
from tasks.models import Task

User = get_user_model()

class RealtimeConsumer(AsyncWebsocketConsumer):
    """Consumer для real-time функціональності"""
    
    async def connect(self):
        """Підключення користувача"""
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Додати користувача до групи онлайн користувачів
        self.online_group = 'online_users'
        await self.channel_layer.group_add(
            self.online_group,
            self.channel_name
        )
        
        # Додати користувача до персональної групи
        self.user_group = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Зареєструвати користувача як онлайн
        await self.set_user_online()
        
        # Повідомити інших користувачів про підключення
        await self.broadcast_user_status('user_connected')
        
        # Надіслати початкові дані
        await self.send_initial_data()
    
    async def disconnect(self, close_code):
        """Відключення користувача"""
        if hasattr(self, 'user') and self.user.is_authenticated:
            # Видалити користувача з онлайн статусу
            await self.set_user_offline()
            
            # Повідомити інших користувачів про відключення
            await self.broadcast_user_status('user_disconnected')
            
            # Покинути групи
            await self.channel_layer.group_discard(
                self.online_group,
                self.channel_name
            )
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Обробка повідомлень від клієнта"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.handle_ping()
            elif message_type == 'task_created':
                await self.handle_task_created(data)
            elif message_type == 'task_updated':
                await self.handle_task_updated(data)
            elif message_type == 'task_deleted':
                await self.handle_task_deleted(data)
            elif message_type == 'page_visit':
                await self.handle_page_visit(data)
            elif message_type == 'get_online_users':
                await self.send_online_users()
            else:
                await self.send_error('Unknown message type')
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON')
        except Exception as e:
            await self.send_error(f'Error processing message: {str(e)}')
    
    async def handle_ping(self):
        """Обробка ping повідомлень для підтримки з'єднання"""
        await self.update_user_activity()
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': timezone.now().isoformat()
        }))

    async def handle_task_created(self, data):
        """Обробка додавання нового завдання"""
        task_id = data.get('task_id')
        if not task_id:
            return
        
        task = await self.get_task(task_id)
        if not task:
            return
        
        # Логувати активність
        await self.log_activity('task_create', f'Створено нове завдання', {
            'task_id': task_id
        })
        
        # Нотифікація (якщо не self-assigned)
        if task.assigned_to and task.assigned_to != self.user:
            await self.send_user_notification(
                task.assigned_to.id,
                'new_task',
                f'Вам призначено завдання: {task.title}',
                {'task_id': task_id}
            )

        # Повідомити користувачів про нове завдання
        await self.broadcast_task_event(
            task,
            {
                'type': 'task_notification',
                'action': 'created',
                'task': await self.serialize_task(task),
                'user': await self.serialize_user(self.user)
            }
        )
    
    async def handle_task_updated(self, data):
        """Обробка оновлення завдання"""
        task_id = data.get('task_id')
        if not task_id:
            return
        
        task = await self.get_task(task_id)
        if not task:
            return
        
        new_status = data.get('status')

        # Логувати активність
        await self.log_activity('task_update', f'Оновлено завдання', {
            'task_id': task_id
        })
        
        # Повідомити власника про завершення завдання
        if (
            new_status == 'Completed' and
            task.assigned_to == self.user and
            task.owner != self.user
        ):
            await self.send_user_notification(
                task.owner.id,
                'task_update',
                f'{self.user.full_name} завершив завдання: {task.title}',
                {'task_id': task_id}
            )

        # Повідомити призначеного про оновлення завдання
        if task.assigned_to and task.assigned_to != self.user:
            await self.send_user_notification(
                task.assigned_to.id,
                'task_update',
                f'Оновлено завдання: {task.title}',
                {
                    'task_id': task_id
                }
            )
        
        await self.broadcast_task_event(
            task,
            {
                'type': 'task_notification',
                'action': 'updated',
                'task': await self.serialize_task(task),
                'user': await self.serialize_user(self.user)
            }
        )

    async def handle_task_deleted(self, data):
        """Обробка видалення завдання"""
        task_id = data.get('task_id')
        if not task_id:
            return

        task = await self.get_task(task_id)
        if not task:
            return

        if task.owner != self.user:
            return

        recipients = await self.get_task_recipients(task_id)

        await self.log_activity('task_delete', 'Видалено завдання', {
            'task_id': task_id
        })

        await self.delete_task(task_id)

        for user_id in recipients:
            await self.channel_layer.group_send(
                f'user_{user_id}',
                {
                    'type': 'task_deleted',
                    'task_id': task_id
                }
            )

    async def handle_page_visit(self, data):
        """Обробка відвідування сторінки"""
        page_url = data.get('url', '')
        page_title = data.get('title', '')
        
        # Оновити поточну сторінку користувача
        await self.update_user_page(page_url)
        
        # Логувати активність
        await self.log_activity('page_visit', f'Відвідав сторінку: {page_title}', {
            'url': page_url,
            'title': page_title
        })
    
    async def send_initial_data(self):
        """Надіслати початкові дані після підключення"""
        online_users = await self.get_online_users_data()
        unread_notifications = await self.get_unread_notifications()
        
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'online_users': online_users,
            'unread_notifications': unread_notifications,
            'user_id': self.user.id
        }))
    
    async def send_online_users(self):
        """Надіслати список онлайн користувачів"""
        online_users = await self.get_online_users_data()
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': online_users
        }))
    
    async def send_error(self, message):
        """Надіслати повідомлення про помилку"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    # Обробники повідомлень від груп
    async def task_notification(self, event):
        """Повідомлення про нове завдання"""
        await self.send(text_data=json.dumps({
            'type': 'task_notification',
            'action': event['action'],
            'task': event['task'],
            'user': event['user']
        }))
    
    async def task_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'task_deleted',
            'task_id': event['task_id']
        }))

    async def user_notification(self, event):
        """Персональне сповіщення користувачу"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_type': event['notification_type'],
            'title': event['title'],
            'message': event['message'],
            'data': event['data']
        }))
    
    async def user_status_update(self, event):
        """Оновлення статусу користувача"""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'action': event['action'],
            'user': event['user'],
            'online_count': event['online_count']
        }))
    
    # Допоміжні методи для роботи з базою даних
    @database_sync_to_async
    def set_user_online(self):
        """Встановити користувача як онлайн"""
        OnlineUser.objects.update_or_create(
            user=self.user,
            defaults={
                'channel_name': self.channel_name,
                'last_activity': timezone.now()
            }
        )
    
    @database_sync_to_async
    def set_user_offline(self):
        """Видалити користувача з онлайн статусу"""
        OnlineUser.objects.filter(user=self.user).delete()
    
    @database_sync_to_async
    def update_user_activity(self):
        """Оновити час останньої активності"""
        OnlineUser.objects.filter(user=self.user).update(
            last_activity=timezone.now()
        )
    
    @database_sync_to_async
    def update_user_page(self, page_url):
        """Оновити поточну сторінку користувача"""
        OnlineUser.objects.filter(user=self.user).update(
            page_url=page_url,
            last_activity=timezone.now()
        )
    
    @database_sync_to_async
    def log_activity(self, activity_type, description, metadata=None):
        """Логувати активність користувача"""
        UserActivity.objects.create(
            user=self.user,
            activity_type=activity_type,
            description=description,
            metadata=metadata or {}
        )

    @database_sync_to_async
    def get_task(self, task_id):
        """Отримати завдання"""
        try:
            return Task.objects.select_related('owner', 'assigned_to').get(id=task_id)
        except Task.DoesNotExist:
            return None
    
    async def broadcast_task_event(self, task, payload):
        recipients = {task.owner.id}

        if task.assigned_to:
            recipients.add(task.assigned_to.id)

        for user_id in recipients:
            await self.channel_layer.group_send(
                f'user_{user_id}',
                payload
            )

    @database_sync_to_async
    def get_task_recipients(self, task_id):
        task = Task.objects.get(id=task_id)
        ids = {task.owner.id}
        if task.assigned_to:
            ids.add(task.assigned_to.id)
        return list(ids)

    @database_sync_to_async
    def delete_task(self, task_id):
        """Видалити завдання"""
        Task.objects.filter(id=task_id).delete()

    @database_sync_to_async
    def get_online_users_data(self):
        """Отримати дані онлайн користувачів"""
        online_users = OnlineUser.get_online_users()
        return [
            {
                'id': ou.user.id,
                'username': ou.user.username,
                'full_name': ou.user.full_name,
                'connected_at': ou.connected_at.isoformat(),
                'page_url': ou.page_url
            }
            for ou in online_users
        ]
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """Отримати непрочитані сповіщення"""
        notifications = RealtimeNotification.objects.filter(
            recipient=self.user,
            is_read=False
        )[:10]
        
        return [
            {
                'id': n.id,
                'type': n.notification_type,
                'title': n.title,
                'message': n.message,
                'data': n.data,
                'created_at': n.created_at.isoformat()
            }
            for n in notifications
        ]

    @database_sync_to_async
    def serialize_task(self, task):
        """Серіалізувати завдання"""
        return {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'owner': {
                'id': task.owner.id,
                'username': task.owner.username,
                'full_name': task.owner.full_name
            },
            'assigned_to': (
                {
                    'id': task.assigned_to.id,
                    'username': task.assigned_to.username,
                    'full_name': task.assigned_to.full_name
                } if task.assigned_to else None
            ),
            'created_at': task.created_at.isoformat()
        }

    @database_sync_to_async
    def serialize_user(self, user):
        """Серіалізувати користувача"""
        return {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name
        }
    
    async def broadcast_user_status(self, action):
        """Повідомити про зміну статусу користувача"""
        online_count = await database_sync_to_async(OnlineUser.get_online_count)()
        
        await self.channel_layer.group_send(
            self.online_group,
            {
                'type': 'user_status_update',
                'action': action,
                'user': await self.serialize_user(self.user),
                'online_count': online_count
            }
        )
    
    async def send_user_notification(self, user_id, notification_type, message, data=None):
        """Надіслати сповіщення конкретному користувачу"""
        # Зберегти в базі даних
        await self.create_notification(user_id, notification_type, message, data)
        
        # Надіслати через WebSocket
        await self.channel_layer.group_send(
            f'user_{user_id}',
            {
                'type': 'user_notification',
                'notification_type': notification_type,
                'title': 'Нове сповіщення',
                'message': message,
                'data': data or {}
            }
        )
    
    @database_sync_to_async
    def create_notification(self, user_id, notification_type, message, data=None):
        """Створити сповіщення в базі даних"""
        RealtimeNotification.objects.create(
            recipient_id=user_id,
            sender=self.user,
            notification_type=notification_type,
            title='Нове сповіщення',
            message=message,
            data=data or {}
        )

