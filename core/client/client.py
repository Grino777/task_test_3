# client/client.py

from pyrogram import Client
from core.settings.settings import settings


class TelegramClient:
    def __init__(self):
        self.client = Client(
            name="sessions/my_bot", api_id=settings.bot_api, api_hash=settings.bot_hash
        )

    async def start(self):
        """
        Запускает клиент Telegram.
        """
        await self.client.start()

    async def stop(self):
        """
        Останавливает клиент Telegram.
        """
        await self.client.stop()

    async def send_message(self, chat_id: int, text: str):
        """
        Отправляет сообщение пользователю.

        :param chat_id: ID чата
        :param text: Текст сообщения
        """
        await self.client.send_message(chat_id, text)

    async def get_chat_history(self, chat_id: int, limit: int = 10):
        """
        Получает историю чатов для указанного пользователя.

        :param chat_id: ID чата
        :param limit: Количество сообщений для получения
        :return: Список сообщений
        """
        chats = [chat async for chat in self.client.get_chat_history(chat_id, limit)]
        return chats
