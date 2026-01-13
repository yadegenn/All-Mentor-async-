import asyncio
from datetime import datetime, timezone

import aiosqlite
import pytz
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import BaseMiddleware
from dataclasses import dataclass
from typing import List, Optional
import html

from telebot.types import Message, MessageID

from ..loader import pool


@dataclass
class User:
    chat_id: int
    topic_id: int
    nickname: str
    username: str
    is_ban: bool
    reg_date: datetime





class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, bot: AsyncTeleBot, group_id: int):
        super().__init__()
        self.update_types = ['message', "message_reaction", "edited_message"]
        self.bot = bot
        self.group_id = group_id


    async def pre_process(self, message, data):
        data['db'] = Database(self.bot, message, self.group_id)

    async def post_process(self, message, data, exception):
        pass  # Соединение с базой данных остается открытым


class Database:
    _global_lock = asyncio.Lock()
    def __init__(self, bot: AsyncTeleBot, message: Message, group_id: int):
        self.bot = bot
        self.message = message
        self.chat_id = message.chat.id
        self.group_id = group_id

    async def get_all_users(self) -> List[User]:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute('SELECT chat_id, topic_id, nickname, username, is_ban, reg_date FROM users')
                rows = await cur.fetchall()

                return [User(chat_id, topic_id, nickname, username, False if is_ban == 0 else True, reg_date) for
                        chat_id, topic_id, nickname, username, is_ban, reg_date in rows]

    # async def get_all_users_without_self(self,database) -> List[User]:
    #     async with database.execute('SELECT chat_id, topic_id, nickname, username, is_ban, reg_date FROM users') as cursor:
    #         rows = await cursor.fetchall()
    #
    #         return [User(chat_id, topic_id, nickname,username,False if is_ban==0 else True,reg_date) for chat_id, topic_id, nickname,username,is_ban,reg_date  in rows]



    async def get_or_create_topic(self, is_thread_not = False) -> int:
        async with self._global_lock:

            async with pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute('SELECT topic_id FROM users WHERE chat_id = %s',(self.chat_id,))
                    row = await cursor.fetchone()
                    if row and row[0]:
                        try:
                            await self.bot.reopen_forum_topic(self.group_id, row[0])
                            return row[0]
                        except Exception as e:
                            if "TOPIC_ID_INVALID" in str(e):
                                # Если топик не существует в Telegram, удаляем его из базы
                                await self.delete_topic_messages(row[0])
                                await cursor.execute('DELETE FROM users WHERE chat_id = %s', (self.chat_id,))
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
                    await cursor.execute('''
                        INSERT INTO users (chat_id, topic_id, nickname, username, reg_date)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (self.chat_id, forum_topic.message_thread_id, nickname,username,datetime.now(timezone.utc)))
                    return forum_topic.message_thread_id

    async def add_message_to_db(self, new_message_id: MessageID | list[Message] | Message, topic_or_chat_id: int, album: list | None):
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                if self.message.chat.id == self.group_id:

                    # Сообщение отправлено в группу
                    topic_id = topic_or_chat_id
                    chat_id = await self.get_chat_id_by_topic_id()

                    # Получаем последний local_id для данного chat_id

                    if isinstance(new_message_id, list):
                        # Вставляем новое сообщение в private_messages
                        for i in new_message_id:
                            await cursor.execute('SELECT MAX(local_id) FROM private_messages WHERE chat_id = %s',(chat_id,))
                            max_local_id = await cursor.fetchone()
                            new_local_id = (max_local_id[0] or 0) + 1
                            await cursor.execute('''
                                INSERT INTO private_messages (chat_id, message_id, local_id)
                                VALUES (%s, %s, %s)
                            ''', (chat_id, i.message_id, new_local_id))
                    else:
                        await cursor.execute('SELECT MAX(local_id) FROM private_messages WHERE chat_id = %s',
                                                   (chat_id,))
                        max_local_id = await cursor.fetchone()
                        new_local_id = (max_local_id[0] or 0) + 1
                        # Вставляем новое сообщение в private_messages
                        await cursor.execute('''
                            INSERT INTO private_messages (chat_id, message_id, local_id)
                            VALUES (%s, %s, %s)
                        ''', (chat_id, new_message_id.message_id, new_local_id))

                    # Получаем последний local_id для данного topic_id

                    if(album):
                        for i in album:
                            await cursor.execute('SELECT MAX(local_id) FROM group_messages WHERE topic_id = %s',
                                                       (topic_id,))
                            max_local_id = await cursor.fetchone()
                            new_local_id = (max_local_id[0] or 0) + 1
                            await cursor.execute('''
                                INSERT INTO group_messages (topic_id, message_id, local_id)
                                VALUES (%s, %s, %s)
                            ''', (topic_id, i.message_id, new_local_id))
                    else:
                        await cursor.execute('SELECT MAX(local_id) FROM group_messages WHERE topic_id = %s',
                                                   (topic_id,))
                        max_local_id = await cursor.fetchone()
                        new_local_id = (max_local_id[0] or 0) + 1
                        # Вставляем оригинальное сообщение в group_messages
                        await cursor.execute('''
                            INSERT INTO group_messages (topic_id, message_id, local_id)
                            VALUES (%s, %s, %s)
                        ''', (topic_id, self.message.message_id, new_local_id))
                else:
                    # Сообщение отправлено в личку
                    chat_id = self.message.chat.id
                    topic_id = await self.get_topic_id_by_chat_id()


                    if isinstance(new_message_id, list):
                        # Вставляем новое сообщение в private_messages
                        for i in new_message_id:
                            # Получаем последний local_id для данного topic_id
                            await cursor.execute('SELECT MAX(local_id) FROM group_messages WHERE topic_id = %s',
                                                       (topic_id,))
                            max_local_id = await cursor.fetchone()
                            new_local_id = (max_local_id[0] or 0) + 1

                            # Вставляем новое сообщение в group_messages
                            await cursor.execute('''
                                INSERT INTO group_messages (topic_id, message_id, local_id)
                                VALUES (%s, %s, %s)
                            ''', (topic_id, i.message_id, new_local_id))
                    else:
                        # Получаем последний local_id для данного topic_id
                        await cursor.execute('SELECT MAX(local_id) FROM group_messages WHERE topic_id = %s',
                                                   (topic_id,))
                        max_local_id = await cursor.fetchone()
                        new_local_id = (max_local_id[0] or 0) + 1

                        # Вставляем новое сообщение в group_messages
                        await cursor.execute('''
                            INSERT INTO group_messages (topic_id, message_id, local_id)
                            VALUES (%s, %s, %s)
                        ''', (topic_id, new_message_id.message_id, new_local_id))

                    if(album):
                        for i in album:
                            # Получаем последний local_id для данного chat_id
                            await cursor.execute('SELECT MAX(local_id) FROM private_messages WHERE chat_id = %s',
                                                       (chat_id,))
                            max_local_id = await cursor.fetchone()
                            new_local_id = (max_local_id[0] or 0) + 1

                            # Вставляем оригинальное сообщение в private_messages
                            await cursor.execute('''
                                INSERT INTO private_messages (chat_id, message_id, local_id)
                                VALUES (%s, %s, %s)
                            ''', (chat_id, i.message_id, new_local_id))
                    else:
                        # Получаем последний local_id для данного chat_id
                        await cursor.execute('SELECT MAX(local_id) FROM private_messages WHERE chat_id = %s',
                                                   (chat_id,))
                        max_local_id = await cursor.fetchone()
                        new_local_id = (max_local_id[0] or 0) + 1

                        # Вставляем оригинальное сообщение в private_messages
                        await cursor.execute('''
                            INSERT INTO private_messages (chat_id, message_id, local_id)
                            VALUES (%s, %s, %s)
                        ''', (chat_id, self.message.message_id, new_local_id))

                

    async def get_group_message_id_by_private_message(self, message_id: int) -> Optional[int]:
        topic_id = await self.get_topic_id_by_chat_id()
        # Сначала находим local_id для переданного message_id в таблице private_messages
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT local_id FROM private_messages WHERE chat_id = %s AND message_id = %s',
                                           (self.message.chat.id, message_id))
                row = await cursor.fetchone()
                if row:
                    local_id = row[0]

                    # Теперь ищем message_id в таблице group_messages, используя topic_id и local_id
                    await cursor.execute('SELECT message_id FROM group_messages WHERE topic_id = %s AND local_id = %s',
                                               (topic_id, local_id))
                    row = await cursor.fetchone()
                    if row:
                        return row[0]
                    else:
                        return None
                else:
                    return None

    async def get_topic_id_by_message_id(self, message_id: int) -> Optional[int]:
        # Ищем message_id в таблице group_messages, чтобы получить topic_id
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT topic_id FROM group_messages WHERE message_id = %s', (message_id,))
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
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT local_id FROM group_messages WHERE topic_id = %s AND message_id = %s',
                                           (topic_id, message_id))
                row = await cursor.fetchone()
                if row:
                    local_id = row[0]

                    # Теперь находим chat_id для переданного topic_id
                    chat_id = await self.get_chat_id_by_topic_id()

                    # Теперь ищем message_id в таблице private_messages, используя chat_id и local_id
                    await cursor.execute('SELECT message_id FROM private_messages WHERE chat_id = %s AND local_id = %s',
                                               (chat_id, local_id))
                    row = await cursor.fetchone()
                    if row:
                        return row[0]
                    else:
                        return None
                else:
                    return None

    async def get_chat_id_by_topic_id(self) -> Optional[int]:
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                if(isinstance(self.message, Message)):
                    await cursor.execute('SELECT chat_id FROM users WHERE topic_id = %s', (self.message.message_thread_id,))
                    row = await cursor.fetchone()
                    if row:
                        return row[0]
                    else:
                        await self.bot.send_message(self.chat_id, "Данный чат перестал функционировать", message_thread_id=self.message.message_thread_id)
                        return None
                else:
                    topic_id = await self.get_topic_id_by_message_id(self.message.message_id)
                    await cursor.execute('SELECT chat_id FROM users WHERE topic_id = %s', (topic_id,))
                    row = await cursor.fetchone()
                    if row:
                        return row[0]
                    else:
                        await self.bot.send_message(self.chat_id, "Данный чат перестал функционировать", message_thread_id=self.message.message_thread_id)
                        return None
    async def get_topic_id_by_chat_id(self) -> Optional[int]:
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT topic_id FROM users WHERE chat_id = %s', (self.message.chat.id,))
                row = await cursor.fetchone()
                if row:
                    return row[0]
                else:
                    await self.bot.send_message(self.chat_id, "Данный чат перестал функционировать", message_thread_id=self.message.message_thread_id)
                    return None

    async def delete_topic_messages(self, topic_id: int):
        # Get chat_id associated with this topic
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT chat_id FROM users WHERE topic_id = %s', (topic_id,))
                row = await cursor.fetchone()
                if row:
                    chat_id = row[0]

                    # Delete all messages from private_messages for this chat_id
                    await cursor.execute('DELETE FROM private_messages WHERE chat_id = %s', (chat_id,))

                # Delete all messages from group_messages for this topic_id
                await cursor.execute('DELETE FROM group_messages WHERE topic_id = %s', (topic_id,))
                

    async def get_user_by_topic_id(self):
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                if(isinstance(self.message, Message)):
                    await cursor.execute('SELECT chat_id, topic_id, nickname, username, is_ban, reg_date FROM users WHERE topic_id = %s', (self.message.message_thread_id,))
                    row = await cursor.fetchone()
                    if row:
                        row = list(row)
                        row[4] = False if row[4] == 0 else True
                        return User(*row)
                    else:
                        await self.bot.send_message(self.chat_id, "Данный чат перестал функционировать", message_thread_id=self.message.message_thread_id)
                        return None
                else:
                    topic_id = await self.get_topic_id_by_message_id(self.message.message_id)
                    await cursor.execute('SELECT chat_id, topic_id, nickname, username, is_ban, reg_date FROM users WHERE topic_id = %s', (topic_id,))
                    row = await cursor.fetchone()
                    if row:
                        row = list(row)
                        row[4] = False if row[4] == 0 else True
                        return User(*row)
                    else:
                        await self.bot.send_message(self.chat_id, "Данный чат перестал функционировать", message_thread_id=self.message.message_thread_id)
                        return None
    async def get_user_by_chat_id(self):
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:

                await cursor.execute('SELECT chat_id, topic_id, nickname, username, is_ban, reg_date FROM users WHERE chat_id = %s',(self.message.chat.id,))

                row = await cursor.fetchone()
                if row:
                    row = list(row)
                    row[4] = False if row[4] == 0 else True
                    return User(*row)
                else:
                    await self.get_or_create_topic()
                    return await self.get_user_by_chat_id()
                    # await self.bot.send_message(self.chat_id, "Данный чат перестал функционировать",
                    #                             message_thread_id=self.message.message_thread_id)
                    # return None
    async def update_ban_status_by_topic_id(self):

        user = await self.get_user_by_topic_id()
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('UPDATE users SET is_ban=%s WHERE topic_id = %s',
                                      (not user.is_ban,self.message.message_thread_id))
                
        if(not user.is_ban==True):
            return "Пользователь заблокирован"
        else:
            return "Пользователь разблокирован"