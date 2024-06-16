from datetime import datetime, timedelta, timezone
from pyrogram import Client
from pyrogram.types import Message
from core.db.db import Database
from core.db.models import User
from core.settings.settings import settings
import asyncio


class MessageFunnel:
    def __init__(self, db, client):
        self.db: Database = db
        self.client: Client = client
        self.db_semaphore = asyncio.Semaphore(
            1
        )  # Семафор для управления доступом к базе данных

    async def process_message(self, message: Message):
        """
        Обрабатывает входящие сообщения и обновляет статус пользователя в базе данных.

        :param message: Входящее сообщение
        """
        user_id = message.from_user.id

        # Проверка на пустое сообщение
        if not message.text:
            return

        async with self.db_semaphore:
            user = await self.db.get_user(user_id)

            if not user:
                # Новый пользователь
                user = User(
                    id=user_id,
                    created_at=datetime.now(timezone.utc),
                    status="alive",
                    status_updated_at=datetime.now(timezone.utc),
                    last_message_sent_at=None,  # Новые пользователи не имеют отправленных сообщений
                )
                await self.db.add_user(user)

        # Мониторинг триггеров
        async for msg in self.client.get_chat_history(user_id):
            if msg.text and (
                "прекрасно" in msg.text.lower() or "ожидать" in msg.text.lower()
            ):
                async with self.db_semaphore:
                    await self.db.update_user_status(
                        user_id, "finished", datetime.now(timezone.utc)
                    )
                return

    async def send_scheduled_messages(self):
        """
        Отправляет запланированные сообщения пользователям.
        """
        current_time = datetime.now(timezone.utc)
        async with self.db_semaphore:
            users_to_message = await self.db.get_users_to_send_messages()
        for user in users_to_message:
            user_id = user["user_id"]
            if (
                user["msg_1"]
                and user["msg_1"] <= current_time
                and not user["status_msg_1"]
            ):
                await self.client.send_message(user_id, settings.msg_1)
                async with self.db_semaphore:
                    await self.db.update_message_status(user_id, 1)
                    await self.db.update_last_message_sent_at(user_id, current_time)
            elif (
                user["msg_2"]
                and user["msg_2"] <= current_time
                and not user["status_msg_2"]
            ):
                await self.client.send_message(user_id, settings.msg_2)
                async with self.db_semaphore:
                    await self.db.update_message_status(user_id, 2)
                    await self.db.update_last_message_sent_at(user_id, current_time)
            elif (
                user["msg_3"]
                and user["msg_3"] <= current_time
                and not user["status_msg_3"]
            ):
                await self.client.send_message(user_id, settings.msg_3)
                async with self.db_semaphore:
                    await self.db.update_message_status(user_id, 3)
                    await self.db.update_last_message_sent_at(user_id, current_time)
