import asyncio

from pyrogram import filters

from core.client.client import TelegramClient
from core.db.db import Database
from core.funnel.funnel import MessageFunnel
from core.settings.settings import settings


async def main():
    db = Database()
    await db.connect()

    client = TelegramClient().client

    funnel = MessageFunnel(db, client)

    @client.on_message(filters.text)
    async def handle_message(client, message):
        await funnel.process_message(message)

    async with client:
        while True:
            await funnel.send_scheduled_messages()
            await asyncio.sleep(10)  # Задержка между проверками на отправку сообщений


if __name__ == "__main__":
    asyncio.run(main())
