from datetime import datetime
from core.settings.settings import settings
from core.db.models import User

class MessageFunnel:
    def __init__(self, db, client):
        self.db = db
        self.client = client

    async def process_message(self, message):
        """
        Обрабатывает входящие сообщения и обновляет статус пользователя в базе данных.

        :param message: Входящее сообщение
        """
        user_id = message.from_user.id
        user = await self.db.get_user(user_id)

        if not user:
            # Новый пользователь
            user = User(
                id=user_id,
                created_at=datetime.utcnow(),
                status="alive",
                status_updated_at=datetime.utcnow(),
                last_message_sent_at=None,  # Новые пользователи не имеют отправленных сообщений
            )
            await self.db.add_user(user)

        # Мониторинг триггеров
        history = await self.client.get_chat_history(user_id)
        for msg in history:
            if msg.text:  # Проверка на пустое сообщение
                if "прекрасно" in msg.text.lower() or "ожидать" in msg.text.lower():
                    await self.db.update_user_status(user_id, "finished", datetime.utcnow())
                    return

    async def send_scheduled_messages(self):
        """
        Отправляет запланированные сообщения пользователям.
        """
        intervals = [
            (settings.interval_1, settings.msg_1),
            (settings.interval_2, settings.msg_2),
            (settings.interval_3, settings.msg_3),
        ]

        # Отправка первого сообщения новым пользователям
        new_users = await self.db.get_new_users()
        for user in new_users:
            await self.client.send_message(user.id, settings.msg_1)
            await self.db.update_last_message_sent_at(user.id, datetime.utcnow())

        # Отправка следующих сообщений пользователям, если интервал прошел
        for interval, message in intervals:
            users = await self.db.get_users_for_message(interval)
            for user in users:
                await self.client.send_message(user.id, message)
                await self.db.update_last_message_sent_at(user.id, datetime.utcnow())
