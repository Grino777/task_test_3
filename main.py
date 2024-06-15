# main.py

import asyncio
from pyrogram import filters
from core.db.db import Database
from core.client.client import TelegramClient
from core.funnel.funnel import MessageFunnel


async def handle_messages(client, funnel):
    @client.client.on_message(filters.private)
    async def on_message(client, message):
        await funnel.process_message(message)


async def main():
    # Инициализация базы данных
    db = Database()
    await db.connect()

    # Инициализация клиента Telegram
    client = TelegramClient()
    await client.start()

    # Инициализация воронки
    funnel = MessageFunnel(db, client)

    # Запуск обработчика входящих сообщений
    await handle_messages(client, funnel)

    try:
        while True:
            # Проверка и отправка запланированных сообщений
            await funnel.send_scheduled_messages()

            # Проверка новых сообщений для каждого пользователя
            users = await db.get_users()
            for user in users:
                messages = await client.get_chat_history(user.id)
                for message in messages:
                    await funnel.process_message(message)

            # Проверяем каждые 60 секунд
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        print("Остановка по запросу пользователя...")

    finally:
        # Остановка клиента Telegram
        await client.stop()

        # Закрытие соединения с базой данных
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
