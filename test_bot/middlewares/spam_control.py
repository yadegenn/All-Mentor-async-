from telebot import BaseMiddleware
from telebot.asyncio_handler_backends import CancelUpdate, ContinueHandling
from telebot.asyncio_helper import ApiTelegramException
import time
import asyncio


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit_albums, limit_messages, time_window, bot) -> None:
        self.album_times = {}  # Счетчик для альбомов
        self.message_times = {}  # Счетчик для обычных сообщений
        self.limit_albums = limit_albums
        self.limit_messages = limit_messages
        self.time_window = time_window
        self.update_types = ['message']
        self.bot = bot
        self.first_messages = {}  # Хранение первых сообщений альбомов
        self.blocked_albums = set()  # Заблокированные альбомы

    def _clean_old_messages(self, user_id: int, current_time: float, is_album: bool = False):
        times_dict = self.album_times if is_album else self.message_times
        if user_id in times_dict:
            times_dict[user_id] = [
                msg_time for msg_time in times_dict[user_id]
                if current_time - msg_time < self.time_window
            ]

    async def pre_process(self, message, data):
        if not hasattr(message, 'from_user') or message.from_user is None:
            return

        user_id = message.from_user.id
        current_time = time.time()

        # Обработка альбома
        if message.media_group_id:
            self._clean_old_messages(user_id, current_time, is_album=True)

            if user_id not in self.album_times:
                self.album_times[user_id] = []

            # Проверяем, заблокирован ли альбом
            if message.media_group_id in self.blocked_albums:
                return CancelUpdate()

            # Если это первое сообщение в альбоме
            if message.media_group_id not in self.first_messages:
                # Проверяем лимит альбомов
                if len(self.album_times[user_id]) >= self.limit_albums:
                    self.blocked_albums.add(message.media_group_id)
                    await asyncio.sleep(self.time_window)
                    # await self.bot.reply_to(
                    #     message,
                    #     f'Пожалуйста, подождите {self.time_window} секунд перед отправкой следующих альбомов'
                    # )
                    return ContinueHandling()
                self.first_messages[message.media_group_id] = message.message_id
                self.album_times[user_id].append(current_time)

            # Очистка словарей если слишком много записей
            if len(self.first_messages) > 1000:
                self.first_messages.clear()
                self.blocked_albums.clear()
            return

        # Обработка обычных сообщений
        self._clean_old_messages(user_id, current_time)

        if user_id not in self.message_times:
            self.message_times[user_id] = []

        if len(self.message_times[user_id]) >= self.limit_messages:
            await asyncio.sleep(self.time_window)
            # await self.bot.reply_to(
            #     message,
            #     f'Пожалуйста, подождите {self.time_window} секунд перед отправкой следующих сообщений'
            # )
            return ContinueHandling()
        self.message_times[user_id].append(current_time)

    async def post_process(self, message, data, exception):
        pass