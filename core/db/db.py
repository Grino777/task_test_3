import asyncpg
from core.settings.settings import settings
from core.db.models import User
from datetime import datetime, timedelta


class Database:
    def __init__(self):
        self.connection = None

    async def connect(self):
        """
        Устанавливает соединение с базой данных и создает таблицу, если она не существует.
        """
        self.connection = await asyncpg.connect(
            user=settings.db_login,
            password=settings.db_pass,
            host=settings.db_ip,
            port=settings.db_port,
            database="task_test_3",
        )
        await self.create_table()

    async def close(self):
        """
        Закрывает соединение с базой данных.
        """
        await self.connection.close()

    async def create_table(self):
        """
        Создает таблицу users, если она не существует.
        """
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL,
                status VARCHAR(10) NOT NULL,
                status_updated_at TIMESTAMPTZ NOT NULL,
                last_message_sent_at TIMESTAMPTZ
            )
        """)

    async def get_user(self, user_id: int) -> User:
        """
        Возвращает пользователя по его ID.

        :param user_id: ID пользователя
        :return: Объект User или None, если пользователь не найден
        """
        query = "SELECT id, created_at, status, status_updated_at, last_message_sent_at FROM users WHERE id = $1"
        result = await self.connection.fetchrow(query, user_id)
        if result:
            return User(**result)
        return None

    async def add_user(self, user: User):
        """
        Добавляет нового пользователя в базу данных.

        :param user: Объект User
        """
        query = """
        INSERT INTO users (id, created_at, status, status_updated_at, last_message_sent_at)
        VALUES ($1, $2, $3, $4, $5)
        """
        await self.connection.execute(
            query,
            user.id,
            user.created_at,
            user.status,
            user.status_updated_at,
            user.last_message_sent_at,
        )

    async def get_new_users(self):
        """
        Возвращает список новых пользователей, у которых нет отправленных сообщений.

        :return: Список объектов User
        """
        query = "SELECT id, created_at, status, status_updated_at, last_message_sent_at FROM users WHERE last_message_sent_at IS NULL"
        results = await self.connection.fetch(query)
        return [User(**result) for result in results]

    async def get_users_for_message(self, interval: int):
        """
        Возвращает пользователей, которым необходимо отправить сообщение, исходя из интервала.

        :param interval: Интервал времени в минутах
        :return: Список объектов User
        """
        check_time = datetime.utcnow() - timedelta(minutes=interval)
        query = """
        SELECT id, created_at, status, status_updated_at, last_message_sent_at
        FROM users
        WHERE status = 'alive' AND (last_message_sent_at IS NULL OR last_message_sent_at < $1)
        """
        results = await self.connection.fetch(query, check_time)
        return [User(**result) for result in results]

    async def update_last_message_sent_at(self, user_id: int, sent_at: datetime):
        """
        Обновляет время отправки последнего сообщения для пользователя.

        :param user_id: ID пользователя
        :param sent_at: Время отправки последнего сообщения
        """
        query = """
        UPDATE users
        SET last_message_sent_at = $2
        WHERE id = $1
        """
        await self.connection.execute(query, user_id, sent_at)

    async def update_user_status(self, user_id: int, status: str, updated_at: datetime):
        """
        Обновляет статус пользователя.

        :param user_id: ID пользователя
        :param status: Новый статус пользователя
        :param updated_at: Время обновления статуса
        """
        query = """
        UPDATE users
        SET status = $2, status_updated_at = $3
        WHERE id = $1
        """
        await self.connection.execute(query, user_id, status, updated_at)
