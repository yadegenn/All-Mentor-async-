import aiosqlite
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import BaseMiddleware, CancelUpdate

from .db import Database


class BanMiddleware(BaseMiddleware):
    def __init__(self, db: aiosqlite.Connection, bot: AsyncTeleBot, group_id: int) -> None:
        super().__init__()
        self.db = db
        self.update_types = ['message', "message_reaction", "edited_message"]
        self.bot = bot
        self.group_id = group_id


    async def pre_process(self, message, data):
        text = getattr(message, 'text', None) or ""
        if (message.chat.type == "private" and not text.startswith("/")):
            database = Database(self.db, self.bot, message, self.group_id)
            user_data = await database.get_user_by_chat_id()
            if (user_data.is_ban):
                return CancelUpdate()

    async def post_process(self, message, data, exception):
        pass