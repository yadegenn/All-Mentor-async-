import asyncio
from typing import Union, Optional
from datetime import datetime, timedelta

import aiosqlite
from telebot import SkipHandler
from telebot.asyncio_handler_backends import BaseMiddleware, CancelUpdate
from telebot.types import Message, MessageReactionUpdated

from utils.db import init_db

user_data = {}
group_data = {}

class UserTimeChecker(BaseMiddleware):
    def __init__(self, group_id, db_path) -> None:
        super().__init__()
        self.update_types = ['message', 'message_reaction']
        self.GROUP_ID = group_id
        self.db_path = db_path
        self.db_object = None


    async def database_init(self):
        self.db_object = await init_db(self.db_path)

    async def get_topic_id_by_chat_id(self, chat_id):
        await self.database_init()
        async with self.db_object.execute('SELECT topic_id FROM users WHERE chat_id = ?', (chat_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def pre_process(self, update, data):
        if isinstance(update, Message):
            await self.process_message(update)
        elif isinstance(update, MessageReactionUpdated):
            await self.process_message_reaction(update)

    async def process_message(self, message: Message):
        if message.chat.type == "private":
            topic_id = await self.get_topic_id_by_chat_id(message.chat.id)
            if str(message.chat.id) in user_data and message.text != "/start":
                user_data[str(message.chat.id)] = "delete"
            elif str(message.chat.id) not in user_data and message.text == "/start":
                user_data[str(message.chat.id)] = datetime.now()
            if topic_id:
                if str(topic_id) not in group_data and message.text != "/start" and message.content_type == "text":
                    group_data[str(topic_id)] = datetime.now()
        elif message.chat.id == self.GROUP_ID:
            if str(message.message_thread_id) in group_data:
                group_data[str(message.message_thread_id)] = "delete"
    async def get_topic_id_by_message_id(self, message_id: int) -> Optional[int]:
        # Ищем message_id в таблице group_messages, чтобы получить topic_id
        async with self.db_object.execute('SELECT topic_id FROM group_messages WHERE message_id = ?', (message_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            else:
                return None
    async def process_message_reaction(self, reaction: MessageReactionUpdated):
        chat_id = reaction.chat.id
        message_id = reaction.message_id
        user_id = reaction.user.id
        if reaction.chat.type == "private":
            topic_id = await self.get_topic_id_by_chat_id(chat_id)
            if topic_id:
                if str(topic_id) not in group_data:
                    group_data[str(topic_id)] = datetime.now()
        elif chat_id == self.GROUP_ID:
            topic_id = await self.get_topic_id_by_message_id(message_id)
            if(topic_id):
                if str(topic_id) in group_data:
                    group_data[str(topic_id)] = "delete"

    async def post_process(self, message, data, exception):
        pass

