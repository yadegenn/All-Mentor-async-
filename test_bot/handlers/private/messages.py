import asyncio
import io
import time
import traceback
from collections import defaultdict, deque
from pydoc import html

import telebot
from telebot.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
from ...loader import bot, GROUP_ID, DEVELOPER_ID
from ...utils.formats import caption_messages, text_message_format
from ...utils.markup_sources import get_content_data


class GlobalQueueManager:
    def __init__(self):
        self.queues = {}
        self.next_process_time = {}
        self.penalized_users = set()  # Те, кто сейчас "отбывает наказание" или "выходит из него"
        self.has_work_event = asyncio.Event()

        # --- ВАШИ НАСТРОЙКИ ---
        self.SPAM_LIMIT = 3  # Если больше 3 сообщений — считаем спамом
        self.PENALTY = 30.0  # Первый бан (тишина)
        self.NORMAL_DELAY = 1.0  # Скорость для нормальных юзеров
        self.BEFORE_BAN_DELAY = 15.0  # Скорость разгребания спама (медленный режим)

    async def add_task(self, user_id, func):
        if user_id not in self.queues:
            self.queues[user_id] = deque()
            if user_id not in self.next_process_time:
                self.next_process_time[user_id] = 0

        self.queues[user_id].append(func)
        self.has_work_event.set()

    async def start_worker(self):
        while True:
            if not self.queues:
                self.has_work_event.clear()
                await self.has_work_event.wait()

            current_time = time.time()
            users_to_cleanup = []
            active_users = list(self.queues.keys())

            for user_id in active_users:
                queue = self.queues[user_id]

                # 1. ПРОВЕРКА ВРЕМЕНИ
                if current_time < self.next_process_time.get(user_id, 0):
                    continue

                    # 2. ЛОВИМ СПАМЕРА
                # Если очередь большая и мы его еще не пометили как "наказанного"
                if len(queue) >= self.SPAM_LIMIT and user_id not in self.penalized_users:
                    # Ставим большой бан (30 сек)
                    self.next_process_time[user_id] = current_time + self.PENALTY
                    self.penalized_users.add(user_id)
                    continue

                    # 3. ОБРАБОТКА СООБЩЕНИЙ
                if queue:
                    task_func = queue.popleft()
                    try:
                        await task_func()
                    except Exception as e:
                        print(f"Error: {e}")

                    # --- ГЛАВНОЕ ИЗМЕНЕНИЕ ЗДЕСЬ ---
                    # Определяем, какую паузу ставить перед СЛЕДУЮЩИМ сообщением

                    if user_id in self.penalized_users:
                        # Если юзер помечен как спамер (разгребает завал)
                        # Используем большую задержку (15 сек)
                        delay = self.BEFORE_BAN_DELAY
                    else:
                        # Если юзер нормальный
                        # Используем обычную задержку (1 сек)
                        delay = self.NORMAL_DELAY

                    # Устанавливаем время следующей отправки
                    self.next_process_time[user_id] = time.time() + delay

                # 4. ОЧИСТКА
                if not queue:
                    users_to_cleanup.append(user_id)
                    # Если юзер всё разгреб — снимаем метку наказания
                    if user_id in self.penalized_users:
                        self.penalized_users.remove(user_id)

            # Чистка словаря очередей
            for user_id in users_to_cleanup:
                if user_id in self.queues and not self.queues[user_id]:
                    del self.queues[user_id]

            await asyncio.sleep(0.1)
manager = GlobalQueueManager()
def queued(handler):
    async def wrapper(message, album: list = None, db=None, new_topic_id=None, *args, **kwargs):
        async def task():
            await handler(message, album, db, new_topic_id, *args, **kwargs)

        await manager.add_task(message.chat.id, task)

    return wrapper

@bot.message_handler(content_types=telebot.util.content_type_media, func=lambda message: message.chat.type == "private" )
@queued
async def private_messages(message, album: list = None, db=None, new_topic_id=None):
    # global weekend, latehour, send_weekend_users, send_latehour_users
    func = None
    attempt = {}


    try:
        if message.caption == "/file_id":
            await bot.reply_to(message, message.photo[-1].file_id or message.document[-1].file_id or message.video[-1].file_id)
        user_data = await db.get_user_by_chat_id()

        topic_id = await db.get_or_create_topic()

        chat_id = message.chat.id
        reply_message_id = None

        # # проверки
        # if(weekend and message.chat.id not in send_weekend_users):
        #     await bot.reply_to(message,"Сегодня вам могут не ответить, так как у сервиса выходной.")
        #     send_weekend_users.append(message.chat.id)
        # else:
        #     if(latehour and message.chat.id not in send_latehour_users):
        #         await bot.reply_to(message,"Сегодня вам уже могут не ответить, так как после 19:00 по московскому времени посредники не работают.")
        #         send_latehour_users.append(message.chat.id)


        if (message.reply_to_message):
            reply_message_id = await db.get_group_message_id_by_private_message(
                int(message.json['reply_to_message']['message_id']))
        if album:
            count_photos = len(album)
            media = []
            user_name = html.escape(message.from_user.username or message.from_user.first_name)
            for i in album:
                result_text, result_entities = caption_messages(i)
                if (i.photo):
                    media.append(InputMediaPhoto(media=i.photo[-1].file_id, caption=result_text if i.caption else i.caption, caption_entities=result_entities if i.caption else i.caption_entities, has_spoiler=i.has_media_spoiler))
                elif(i.video):
                    media.append(InputMediaVideo(media=i.video.file_id, caption=result_text if i.caption else i.caption, caption_entities=result_entities if i.caption else i.caption_entities, has_spoiler=i.has_media_spoiler))
                elif (i.document):
                    media.append(InputMediaDocument(media=i.document.file_id, caption=result_text if i.caption else i.caption, caption_entities=result_entities if i.caption else i.caption_entities))
                elif (i.audio):
                    media.append(InputMediaAudio(media=i.audio.file_id, caption=result_text if i.caption else i.caption,
                                                    caption_entities=result_entities if i.caption else i.caption_entities))
            func = lambda: bot.send_media_group(chat_id=GROUP_ID,media=media,message_thread_id=topic_id,reply_to_message_id=reply_message_id)
            await db.add_message_to_db(await func(), topic_id, album)
            attempt[message.chat.id] = None
        else:

            content_data = get_content_data(message)

            if message.content_type in content_data:
                data = content_data[message.content_type]

                if data["file_id"]:  # Если file_id определен
                    result_text, result_entities = caption_messages(message)


                    # Вызываем соответствующую функцию
                    func = lambda: data["send_function"](
                        chat_id=GROUP_ID,
                        caption=result_text,
                        caption_entities=result_entities,
                        message_thread_id=topic_id,

                        reply_to_message_id = reply_message_id,
                        **{str(data["send_param"]): data["file_id"]},
                        **{str(data["spoiler_param"]): message.has_media_spoiler} if data["spoiler_param"] and data["spoiler_param"].lower() != "none" else {}
                    )
                    await db.add_message_to_db(await func(),topic_id, None)
                    attempt[message.chat.id] = None
            elif(message.content_type == "text"):
                result_text, result_entities = text_message_format(message)
                func = lambda: bot.send_message(chat_id=GROUP_ID, text=result_text, entities=result_entities,
                                       message_thread_id=topic_id, reply_to_message_id=reply_message_id)
                await db.add_message_to_db(await func(),topic_id, None)
                attempt[message.chat.id] = None

            else:
                result_text, result_entities = caption_messages(message)
                func = lambda: bot.copy_message(chat_id=GROUP_ID, caption=result_text, caption_entities=result_entities, from_chat_id=message.chat.id, reply_to_message_id=reply_message_id, message_id=message.message_id, message_thread_id=topic_id)
                await db.add_message_to_db(await func(), topic_id, None)
                attempt[message.chat.id] = None

    except Exception as e:
        if "message to be replied not found" in str(e):
            await bot.reply_to(message,
                               "Ваше сообщение не было доставлено, так как мы не смогли найти оригинальное сообщение. Возможно, оно было удалено, являлось рассылкой, сообщением бота или недавно произошло обновление и старые сообщения больше не функциональны. Попробуйте отправить его еще раз без ответа на это сообщение или ответить на соседнее сообщение.")
        elif "message thread not found" in str(e):
            await db.delete_topic_messages(topic_id)
            new_topic = await db.get_or_create_topic(is_thread_not=True)
            await private_messages(message,album,db, new_topic)
        # elif "Too Many Requests" in str(e):
        #     await bot.reply_to(message,
        #                        "Ваше сообщение не было доставлено, вы отправляли сообщения слишком часто, подождите некоторое время перед отправкой")
        else:
            error_message = traceback.format_exc()
            error_file = io.BytesIO(error_message.encode('utf-8'))
            error_file.name = "error_log.txt"
            error_file.seek(0)
            await bot.send_document(chat_id=DEVELOPER_ID,document=error_file,caption=f"Ошибка при отправке сообщения от пользователя  {message.from_user.username or message.from_user.first_name} ({message.chat.id})")

