from telebot import BaseMiddleware
from telebot.asyncio_handler_backends import CancelUpdate
from telebot.asyncio_helper import ApiTelegramException
import time
import asyncio



class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit, time_window, bot) -> None:
        self.message_times = {}
        self.limit = limit
        self.time_window = time_window
        self.update_types = ['message']
        self.bot = bot
        self.processed_albums = set()

    def _clean_old_messages(self, user_id: int, current_time: float):
        if user_id in self.message_times:
            self.message_times[user_id] = [
                msg_time for msg_time in self.message_times[user_id]
                if current_time - msg_time < self.time_window
            ]

    async def pre_process(self, message, data):
        if not hasattr(message, 'from_user') or message.from_user is None:
            return

        user_id = message.from_user.id
        current_time = time.time()

        if message.media_group_id:
            if message.media_group_id in self.processed_albums:
                return CancelUpdate()
            self.processed_albums.add(message.media_group_id)
            if len(self.processed_albums) > 1000:
                self.processed_albums.clear()

        self._clean_old_messages(user_id, current_time)

        if user_id not in self.message_times:
            self.message_times[user_id] = []

        if len(self.message_times[user_id]) >= self.limit:
            await self.bot.reply_to(
                message,
                f'Пожалуйста, подождите {self.time_window} секунд перед отправкой следующих сообщений'
            )
            return CancelUpdate()

        self.message_times[user_id].append(current_time)

    async def post_process(self, message, data, exception):
        pass