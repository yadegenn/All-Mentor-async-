from telebot import BaseMiddleware
from telebot.asyncio_handler_backends import CancelUpdate


class SimpleMiddleware(BaseMiddleware):
    def __init__(self, limit, bot) -> None:
        self.messages_count = {}  # Счетчик сообщений
        self.limit = limit  # Максимальное количество сообщений
        self.update_types = ['message']
        self.bot = bot
        self.processed_albums = set()

    async def pre_process(self, message, data):
        # Пропускаем сервисные сообщения
        if not hasattr(message, 'from_user') or message.from_user is None:
            return

        user_id = message.from_user.id

        # Обработка альбомов
        if message.media_group_id:
            if message.media_group_id in self.processed_albums:
                return CancelUpdate()
            self.processed_albums.add(message.media_group_id)
            if len(self.processed_albums) > 1000:  # Очистка памяти
                self.processed_albums.clear()

        # Инициализация счетчика для нового пользователя
        if user_id not in self.messages_count:
            self.messages_count[user_id] = 1
            return

        # Проверка на превышение лимита
        if self.messages_count[user_id] >= self.limit:
            await self.bot.reply_to(message, 'Пожалуйста, подождите немного перед отправкой следующих сообщений')
            return CancelUpdate()

        # Увеличение счетчика
        self.messages_count[user_id] += 1

    async def post_process(self, message, data, exception):
        pass