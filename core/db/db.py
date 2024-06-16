import asyncpg
from core.settings.settings import settings
from core.db.models import User
from datetime import datetime, timedelta


class Database:
    def __init__(self):
        self.connection = None

    async def connect(self):
        """
        Устанавливает соединение с базой данных.
        """
        self.connection = await asyncpg.connect(
            user=settings.db_login,
            password=settings.db_pass,
            host=settings.db_ip,
            port=settings.db_port,
            database="task_test_3",
        )

        # Создание таблицы пользователей, если она не существует
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY UNIQUE,
                created_at TIMESTAMPTZ NOT NULL,
                status TEXT NOT NULL,
                status_updated_at TIMESTAMPTZ NOT NULL,
                last_message_sent_at TIMESTAMPTZ
            );
        """)

        # Создание таблицы для сообщений, если она не существует
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(id),
                msg_1 TIMESTAMPTZ,
                status_msg_1 BOOLEAN NOT NULL DEFAULT FALSE,
                msg_2 TIMESTAMPTZ,
                status_msg_2 BOOLEAN NOT NULL DEFAULT FALSE,
                msg_3 TIMESTAMPTZ,
                status_msg_3 BOOLEAN NOT NULL DEFAULT FALSE,
                UNIQUE (user_id)
            );
        """)

    async def close(self):
        """
        Закрывает соединение с базой данных.
        """
        await self.connection.close()

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
        async with self.connection.transaction():
            # Добавляем пользователя в таблицу users
            query_users = """
                INSERT INTO users (id, created_at, status, status_updated_at, last_message_sent_at)
                VALUES ($1, $2, $3, $4, $5)
            """
            await self.connection.execute(
                query_users,
                user.id,
                user.created_at,
                user.status,
                user.status_updated_at,
                user.last_message_sent_at,
            )

            # Вычисление времени следующей отправки для каждого сообщения
            current_time = datetime.utcnow()
            interval_1_seconds = settings.interval_1
            interval_2_seconds = settings.interval_2
            interval_3_seconds = settings.interval_3

            next_message_time_1 = current_time + timedelta(seconds=interval_1_seconds)
            next_message_time_2 = next_message_time_1 + timedelta(
                seconds=interval_2_seconds
            )
            next_message_time_3 = next_message_time_2 + timedelta(
                seconds=interval_3_seconds
            )

            # Добавление времени следующей отправки в таблицу messages
            query_messages = """
                INSERT INTO messages (user_id, msg_1, msg_2, msg_3)
                VALUES ($1, $2, $3, $4)
            """
            await self.connection.execute(
                query_messages,
                user.id,
                next_message_time_1,
                next_message_time_2,
                next_message_time_3,
            )

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

    async def update_last_message_sent_at(self, user_id: int, sent_at: datetime):
        """
        Обновляет время отправки последнего сообщения пользователя.

        :param user_id: ID пользователя
        :param sent_at: Время отправки сообщения
        """
        query = """
        UPDATE users
        SET last_message_sent_at = $2
        WHERE id = $1
        """
        await self.connection.execute(query, user_id, sent_at)

    async def get_user_msg_times(self, user_id: int):
        """
        Возвращает время следующей отправки сообщений для пользователя.

        :param user_id: ID пользователя
        :return: Кортеж из времени следующей отправки для msg_1, msg_2 и msg_3
        """
        query = """
        SELECT msg_1, msg_2, msg_3
        FROM messages
        WHERE user_id = $1
        """
        result = await self.connection.fetchrow(query, user_id)
        if result:
            return {
                "msg_1": result["msg_1"],
                "msg_2": result["msg_2"],
                "msg_3": result["msg_3"],
            }
        return {"msg_1": None, "msg_2": None, "msg_3": None}

    async def get_new_users(self):
        """
        Возвращает новых пользователей, которые еще не получили первое сообщение.
        """
        query = """
        SELECT id, created_at, status, status_updated_at, last_message_sent_at
        FROM users
        WHERE last_message_sent_at IS NULL AND status = 'alive'
        """
        results = await self.connection.fetch(query)
        return [User(**result) for result in results]

    async def get_users_for_message(self, interval: timedelta):
        """
        Возвращает пользователей, которым необходимо отправить следующее сообщение.

        :param interval: Интервал времени с момента последнего отправленного сообщения
        """
        interval_seconds = int(interval.total_seconds())
        query = f"""
        SELECT u.id, u.created_at, u.status, u.status_updated_at, u.last_message_sent_at
        FROM users u
        JOIN messages m ON u.id = m.user_id
        WHERE u.status = 'alive' AND (
            (m.msg_1 IS NULL OR m.msg_1 <= NOW() - INTERVAL '{interval_seconds} seconds') OR
            (m.msg_2 IS NULL OR m.msg_2 <= NOW() - INTERVAL '{interval_seconds} seconds') OR
            (m.msg_3 IS NULL OR m.msg_3 <= NOW() - INTERVAL '{interval_seconds} seconds')
        )
        """
        results = await self.connection.fetch(query)
        return [User(**result) for result in results]

    async def get_users_to_send_messages(self):
        """
        Возвращает пользователей, которым необходимо отправить сообщения.
        """
        query = """
        SELECT m.user_id, u.status, m.msg_1, m.status_msg_1, m.msg_2, m.status_msg_2, m.msg_3, m.status_msg_3
        FROM messages m
        JOIN users u ON m.user_id = u.id
        WHERE u.status = 'alive' AND (
            (m.msg_1 IS NOT NULL AND m.msg_1 <= NOW() AND m.status_msg_1 = FALSE) OR
            (m.msg_2 IS NOT NULL AND m.msg_2 <= NOW() AND m.status_msg_2 = FALSE) OR
            (m.msg_3 IS NOT NULL AND m.msg_3 <= NOW() AND m.status_msg_3 = FALSE)
        )
        """
        results = await self.connection.fetch(query)
        return results

    async def update_message_status(self, user_id: int, msg_number: int):
        """
        Обновляет статус отправленного сообщения для пользователя.

        :param user_id: ID пользователя
        :param msg_number: Номер сообщения (1, 2 или 3)
        """
        query = f"""
        UPDATE messages
        SET status_msg_{msg_number} = TRUE
        WHERE user_id = $1
        """
        await self.connection.execute(query, user_id)
