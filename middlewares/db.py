import asyncio
from datetime import datetime

import aiosqlite
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import BaseMiddleware
from dataclasses import dataclass
from typing import List, Optional
import html

from telebot.types import Message, MessageID


@dataclass
class User:
    chat_id: int
    topic_id: int
    nickname: str
    username: str
    is_ban: bool
    reg_date: datetime


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db: aiosqlite.Connection, bot: AsyncTeleBot, group_id: int):
        super().__init__()
        self.db = db
        self.update_types = ['message', "message_reaction", "edited_message"]
        self.bot = bot
        self.group_id = group_id


    async def pre_process(self, message, data):
        data['db'] = Database(self.db, self.bot, message, self.group_id)

    async def post_process(self, message, data, exception):
        pass  # Соединение с базой данных остается открытым


class Database:
    _global_lock = asyncio.Lock()
    def __init__(self, db, bot: AsyncTeleBot, message: Message, group_id: int):
        self.db = db
        self.bot = bot
        self.message = message
        self.chat_id = message.chat.id
        self.group_id = group_id

    async def get_all_users(self) -> List[User]:
        async with self.db.execute('SELECT chat_id, topic_id, nickname, username, is_ban, reg_date FROM users') as cursor:
            rows = await cursor.fetchall()
            return [User(chat_id, topic_id, nickname,username,is_ban,reg_date) for chat_id, topic_id, nickname,username,is_ban,reg_date  in rows]

    # async def add_or_update_user(self, user_name: str, topic_id: int):
    #     await self.db.execute('''
    #         INSERT OR REPLACE INTO users (chat_id, topic_id, user_name)
    #         VALUES (?, ?, ?)
    #     ''', (self.chat_id, topic_id, user_name))
    #     await self.db.commit()

    async def get_or_create_topic(self, is_thread_not = False) -> int:
        async with self._global_lock:

            # Проверяем существующий топик
            async with self.db.execute(
                    'SELECT topic_id FROM users WHERE chat_id = ?',
                    (self.chat_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    try:
                        # Проверяем, существует ли топик в Telegram
                        await self.bot.reopen_forum_topic(self.group_id, row[0])
                        # user_name = html.escape(self.message.from_user.username or self.message.from_user.first_name)
                        # await self.bot.edit_message_text("...", message.chat.id, message.message_id)
                        # await self.bot.delete_message(message.chat.id, message.message_id)
                        return row[0]
                    except Exception as e:
                        if "TOPIC_ID_INVALID" in str(e):
                            # Если топик не существует в Telegram, удаляем его из базы
                            await self.delete_topic_messages(row[0])
                            await self.db.execute('DELETE FROM users WHERE chat_id = ?', (self.chat_id,))
                            await self.db.commit()
                        elif "TOPIC_NOT_MODIFIED" in str(e):
                            return row[0]
                        else:
                            raise

            # Создаём новый топик
            topic_name = html.escape(self.message.from_user.username or self.message.from_user.first_name)

            forum_topic = await self.bot.create_forum_topic(self.group_id, topic_name)
            nickname = html.escape(f"{self.message.from_user.first_name or ''} {self.message.from_user.last_name or ''}")
            username = html.escape(f"{self.message.from_user.username or ''}")
            # Сохраняем новый топик в базу
            await self.db.execute('''
                INSERT INTO users (chat_id, topic_id, nickname, username, reg_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.chat_id, forum_topic.message_thread_id, nickname,username,datetime.now()))

            await self.db.commit()
            return forum_topic.message_thread_id

    async def add_message_to_db(self, new_message_id: MessageID | list[Message] | Message, topic_or_chat_id: int, album: list | None):
        if self.message.chat.id == self.group_id:

            # Сообщение отправлено в группу
            topic_id = topic_or_chat_id
            chat_id = await self.get_chat_id_by_topic_id()

            # Получаем последний local_id для данного chat_id

            if isinstance(new_message_id, list):
                # Вставляем новое сообщение в private_messages
                for i in new_message_id:
                    async with self.db.execute('SELECT MAX(local_id) FROM private_messages WHERE chat_id = ?',
                                               (chat_id,)) as cursor:
                        max_local_id = await cursor.fetchone()
                        new_local_id = (max_local_id[0] or 0) + 1
                    await self.db.execute('''
                        INSERT INTO private_messages (chat_id, message_id, local_id)
                        VALUES (?, ?, ?)
                    ''', (chat_id, i.message_id, new_local_id))
            else:
                async with self.db.execute('SELECT MAX(local_id) FROM private_messages WHERE chat_id = ?',
                                           (chat_id,)) as cursor:
                    max_local_id = await cursor.fetchone()
                    new_local_id = (max_local_id[0] or 0) + 1
                # Вставляем новое сообщение в private_messages
                await self.db.execute('''
                    INSERT INTO private_messages (chat_id, message_id, local_id)
                    VALUES (?, ?, ?)
                ''', (chat_id, new_message_id.message_id, new_local_id))

            # Получаем последний local_id для данного topic_id

            if(album):
                for i in album:
                    async with self.db.execute('SELECT MAX(local_id) FROM group_messages WHERE topic_id = ?',
                                               (topic_id,)) as cursor:
                        max_local_id = await cursor.fetchone()
                        new_local_id = (max_local_id[0] or 0) + 1
                    await self.db.execute('''
                        INSERT INTO group_messages (topic_id, message_id, local_id)
                        VALUES (?, ?, ?)
                    ''', (topic_id, i.message_id, new_local_id))
            else:
                async with self.db.execute('SELECT MAX(local_id) FROM group_messages WHERE topic_id = ?',
                                           (topic_id,)) as cursor:
                    max_local_id = await cursor.fetchone()
                    new_local_id = (max_local_id[0] or 0) + 1
                # Вставляем оригинальное сообщение в group_messages
                await self.db.execute('''
                    INSERT INTO group_messages (topic_id, message_id, local_id)
                    VALUES (?, ?, ?)
                ''', (topic_id, self.message.message_id, new_local_id))
        else:
            # Сообщение отправлено в личку
            chat_id = self.message.chat.id
            topic_id = await self.get_topic_id_by_chat_id()


            if isinstance(new_message_id, list):
                # Вставляем новое сообщение в private_messages
                for i in new_message_id:
                    # Получаем последний local_id для данного topic_id
                    async with self.db.execute('SELECT MAX(local_id) FROM group_messages WHERE topic_id = ?',
                                               (topic_id,)) as cursor:
                        max_local_id = await cursor.fetchone()
                        new_local_id = (max_local_id[0] or 0) + 1

                    # Вставляем новое сообщение в group_messages
                    await self.db.execute('''
                        INSERT INTO group_messages (topic_id, message_id, local_id)
                        VALUES (?, ?, ?)
                    ''', (topic_id, i.message_id, new_local_id))
            else:
                # Получаем последний local_id для данного topic_id
                async with self.db.execute('SELECT MAX(local_id) FROM group_messages WHERE topic_id = ?',
                                           (topic_id,)) as cursor:
                    max_local_id = await cursor.fetchone()
                    new_local_id = (max_local_id[0] or 0) + 1

                # Вставляем новое сообщение в group_messages
                await self.db.execute('''
                    INSERT INTO group_messages (topic_id, message_id, local_id)
                    VALUES (?, ?, ?)
                ''', (topic_id, new_message_id.message_id, new_local_id))

            if(album):
                for i in album:
                    # Получаем последний local_id для данного chat_id
                    async with self.db.execute('SELECT MAX(local_id) FROM private_messages WHERE chat_id = ?',
                                               (chat_id,)) as cursor:
                        max_local_id = await cursor.fetchone()
                        new_local_id = (max_local_id[0] or 0) + 1

                    # Вставляем оригинальное сообщение в private_messages
                    await self.db.execute('''
                        INSERT INTO private_messages (chat_id, message_id, local_id)
                        VALUES (?, ?, ?)
                    ''', (chat_id, i.message_id, new_local_id))
            else:
                # Получаем последний local_id для данного chat_id
                async with self.db.execute('SELECT MAX(local_id) FROM private_messages WHERE chat_id = ?',
                                           (chat_id,)) as cursor:
                    max_local_id = await cursor.fetchone()
                    new_local_id = (max_local_id[0] or 0) + 1

                # Вставляем оригинальное сообщение в private_messages
                await self.db.execute('''
                    INSERT INTO private_messages (chat_id, message_id, local_id)
                    VALUES (?, ?, ?)
                ''', (chat_id, self.message.message_id, new_local_id))

        await self.db.commit()

    # async def create_new_topic(self) -> int:
    #     topic_name = html.escape(self.message.from_user.username or self.message.from_user.first_name)
    #     forum_topic = await self.bot.create_forum_topic(self.group_id, topic_name)
    #
    #     # Delete existing record first
    #     await self.db.execute('''
    #         DELETE FROM users
    #         WHERE chat_id = ?
    #     ''', (self.chat_id,))
    #
    #     # Then insert the new record
    #     await self.db.execute('''
    #         INSERT INTO users (chat_id, topic_id, user_name)
    #         VALUES (?, ?, ?)
    #     ''', (self.chat_id, forum_topic.message_thread_id, topic_name))
    #
    #     await self.db.commit()
    #
    #     return forum_topic.message_thread_id

    async def get_group_message_id_by_private_message(self, message_id: int) -> Optional[int]:
        topic_id = await self.get_topic_id_by_chat_id()
        # Сначала находим local_id для переданного message_id в таблице private_messages
        async with self.db.execute('SELECT local_id FROM private_messages WHERE chat_id = ? AND message_id = ?',
                                   (self.message.chat.id, message_id)) as cursor:
            row = await cursor.fetchone()
            if row:
                local_id = row[0]

                # Теперь ищем message_id в таблице group_messages, используя topic_id и local_id
                async with self.db.execute('SELECT message_id FROM group_messages WHERE topic_id = ? AND local_id = ?',
                                           (topic_id, local_id)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return row[0]
                    else:
                        return None
            else:
                return None

    async def get_topic_id_by_message_id(self, message_id: int) -> Optional[int]:
        # Ищем message_id в таблице group_messages, чтобы получить topic_id
        async with self.db.execute('SELECT topic_id FROM group_messages WHERE message_id = ?', (message_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            else:
                return None

    async def get_private_message_id_by_group_message(self, message_id: int) -> Optional[int]:
        # Сначала находим local_id для переданного message_id в таблице group_messages
        topic_id = None
        if(isinstance(self.message, Message)):
            topic_id = self.message.message_thread_id
        else:
            topic_id = await self.get_topic_id_by_message_id(self.message.message_id)
        async with self.db.execute('SELECT local_id FROM group_messages WHERE topic_id = ? AND message_id = ?',
                                   (topic_id, message_id)) as cursor:
            row = await cursor.fetchone()
            if row:
                local_id = row[0]

                # Теперь находим chat_id для переданного topic_id
                chat_id = await self.get_chat_id_by_topic_id()

                # Теперь ищем message_id в таблице private_messages, используя chat_id и local_id
                async with self.db.execute('SELECT message_id FROM private_messages WHERE chat_id = ? AND local_id = ?',
                                           (chat_id, local_id)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return row[0]
                    else:
                        return None
            else:
                return None

    async def get_chat_id_by_topic_id(self) -> Optional[int]:
        if(isinstance(self.message, Message)):
            async with self.db.execute('SELECT chat_id FROM users WHERE topic_id = ?', (self.message.message_thread_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                else:
                    await self.bot.send_message(self.chat_id, "Данный чат перестал функционировать", message_thread_id=self.message.message_thread_id)
                    return None
        else:
            topic_id = await self.get_topic_id_by_message_id(self.message.message_id)
            async with self.db.execute('SELECT chat_id FROM users WHERE topic_id = ?', (topic_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                else:
                    await self.bot.send_message(self.chat_id, "Данный чат перестал функционировать", message_thread_id=self.message.message_thread_id)
                    return None
    async def get_topic_id_by_chat_id(self) -> Optional[int]:
        async with self.db.execute('SELECT topic_id FROM users WHERE chat_id = ?', (self.message.chat.id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            else:
                await self.bot.send_message(self.chat_id, "Данный чат перестал функционировать", message_thread_id=self.message.message_thread_id)
                return None

    async def delete_topic_messages(self, topic_id: int):
        # Get chat_id associated with this topic
        async with self.db.execute('SELECT chat_id FROM users WHERE topic_id = ?', (topic_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                chat_id = row[0]

                # Delete all messages from private_messages for this chat_id
                await self.db.execute('DELETE FROM private_messages WHERE chat_id = ?', (chat_id,))

        # Delete all messages from group_messages for this topic_id
        await self.db.execute('DELETE FROM group_messages WHERE topic_id = ?', (topic_id,))
        await self.db.commit()