from typing import Optional
from datetime import datetime

from telebot.asyncio_handler_backends import BaseMiddleware
from telebot.types import Message, MessageReactionUpdated

from ..loader import pool
from ..utils.waits_func import weekday_personal
from ..utils.db import init_db, add_user_week_period, get_all_user_week_period

user_reminder = {}
user_weekday_period = {}
async def init_checker():
    for i in await get_all_user_week_period():
        user_weekday_period[str(i.chat_id)] = i.date
class UserTimeChecker(BaseMiddleware):
    def __init__(self, group_id) -> None:
        super().__init__()
        self.update_types = ['message', 'message_reaction']
        self.GROUP_ID = group_id



    # async def get_topic_id_by_chat_id(self, chat_id):
    #     await init_db()
    #     async with pool.connection() as conn:
    #         async with conn.cursor() as cursor:
    #             await cursor.execute('SELECT topic_id FROM users WHERE chat_id = %s', (chat_id,))
    #             row = await cursor.fetchone()
    #             return row[0] if row else None

    async def pre_process(self, update, data):
        if isinstance(update, Message):
            await self.process_message(update)
        # elif isinstance(update, MessageReactionUpdated):
        #     await self.process_message_reaction(update)

    async def process_message(self, message: Message):
        await init_checker()
        if message.chat.type == "private":
            text = getattr(message, 'text', None) or ""
            # topic_id = await self.get_topic_id_by_chat_id(message.chat.id)

            if str(message.chat.id) not in user_reminder and text.startswith("/start"):
                user_reminder[str(message.chat.id)] = datetime.now()
            if str(message.chat.id) not in user_weekday_period and not text.startswith("/"):
                await weekday_personal(message)
                time_now = datetime.now()
                await add_user_week_period(str(message.chat.id), time_now)
                user_weekday_period[str(message.chat.id)] = time_now

        #     if topic_id:
        #         if str(topic_id) not in group_data and not text.startswith("/") and message.content_type == "text":
        #             group_data[str(topic_id)] = datetime.now()
        # elif message.chat.id == self.GROUP_ID:
        #     if str(message.message_thread_id) in group_data:
        #         group_data[str(message.message_thread_id)] = "delete"
    # async def get_topic_id_by_message_id(self, message_id: int) -> Optional[int]:
    #     # Ищем message_id в таблице group_messages, чтобы получить topic_id
    #     async with self.db_object.execute('SELECT topic_id FROM group_messages WHERE message_id = ?', (message_id,)) as cursor:
    #         row = await cursor.fetchone()
    #         if row:
    #             return row[0]
    #         else:
    #             return None
    # async def process_message_reaction(self, reaction: MessageReactionUpdated):
    #     chat_id = reaction.chat.id
    #     message_id = reaction.message_id
    #     user_id = reaction.user.id
    #     if reaction.chat.type == "private":
    #         topic_id = await self.get_topic_id_by_chat_id(chat_id)
    #         if topic_id:
    #             if str(topic_id) not in group_data:
    #                 group_data[str(topic_id)] = datetime.now()
    #     elif chat_id == self.GROUP_ID:
    #         topic_id = await self.get_topic_id_by_message_id(message_id)
    #         if(topic_id):
    #             if str(topic_id) in group_data:
    #                 group_data[str(topic_id)] = "delete"

    async def post_process(self, message, data, exception):
        pass

