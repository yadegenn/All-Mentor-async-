import asyncio
from io import StringIO

import aiofiles
import aiosqlite
import pandas as pd
from telebot.states import StatesGroup, State
from telebot.states.asyncio import StateContext
import traceback

import telebot
from telebot.types import InputMediaVideo, InputMediaDocument

from test_bot.loader import DEVELOPER_ID, ADMINS, db_path, prefix_folder
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto


from test_bot.loader import bot
from test_bot.utils.translator import translator_create_or_update


class AdminStates(StatesGroup):
    upload_data = State()
    upload_front = State()
    spam = State()

@bot.message_handler(commands=['admin'], func=lambda message: message.chat.type == "private" )
async def handle_admin(message):
    if message.chat.id in ADMINS:
        db_main = await aiosqlite.connect(db_path)
        user_count = None
        async with db_main.execute('SELECT COUNT(*) FROM users') as cursor:
            row = await cursor.fetchone()
            if(row):
                user_count = row[0]
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Данные:", callback_data="front"),
                ],
                [
                    InlineKeyboardButton("Получить", callback_data="get_data"),
                    InlineKeyboardButton("Загрузить", callback_data="upload_data")
                ],
                [
                    InlineKeyboardButton("Разметка:",callback_data="front"),
                ],
                [
                    InlineKeyboardButton("Получить", callback_data="get_front"),
                    InlineKeyboardButton("Загрузить", callback_data="upload_front"),
                    InlineKeyboardButton("Откатить", callback_data="last_front")
                ],
                [
                    InlineKeyboardButton("Рассылка", callback_data="broadcast")
                ]
            ],
            3
        )

        await bot.send_message(message.chat.id, f"Админ панель\nКоличество пользователей: {user_count}", reply_markup=markup)
    else:
        await bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")


@bot.callback_query_handler(func=lambda call: call.data in ["get_data", "get_front", "last_front", "upload_data","upload_front", "broadcast"])
async def handle_admin_callback(call, state: StateContext):
    if call.message.chat.id in ADMINS:
        if call.data == "get_data":
            db_main = await aiosqlite.connect(db_path)
            async with db_main.execute('SELECT * FROM users') as cursor:
                rows = await cursor.fetchall()

            # Создание DataFrame
            df = pd.DataFrame(rows, columns=['chat_id', 'topic_id', 'user_name'])

            # Сохранение данных в файл .txt
            df.to_csv('user_topics.txt', sep=' ', index=False)

            # Отправка файла пользователю
            with open('user_topics.txt', 'rb') as file:
                await bot.send_document(call.message.chat.id, file)
        elif call.data == "get_front":
            with open(f'{prefix_folder}locales/ru.ftl', 'rb') as file:
                await bot.send_document(call.message.chat.id, file)
        elif call.data == "upload_data":
            await bot.send_message(call.message.chat.id, "Пожалуйста, загрузите файл txt с данными.")
            await state.set(AdminStates.upload_data)
        elif call.data == "upload_front":
            await bot.send_message(call.message.chat.id, "Пожалуйста, загрузите файл ftl с разметкой.")
            await state.set(AdminStates.upload_front)
        elif call.data == "last_front":
            async with aiofiles.open(f'{prefix_folder}locales/last_ru.ftl', 'r', encoding='utf-8') as file:
                data = await file.read()

            async with aiofiles.open(f'{prefix_folder}locales/ru.ftl', 'w') as new_file:
                await new_file.write(data)
            translator_create_or_update()
            await bot.send_message(call.message.chat.id, "Разметка успешно откатилась.")
        elif call.data == "broadcast":
            await bot.send_message(call.message.chat.id, "Отправьте сообщение и оно будет разослано")
            await state.set(AdminStates.spam)
    else:
        await bot.send_message(call.message.chat.id, "У вас нет доступа к этой функции.")

@bot.message_handler(state=AdminStates.upload_front, content_types=['document'])
async def handle_front(message, state: StateContext):
   if message.chat.id in ADMINS and message.document.mime_type == 'text/plain' and message.document.file_name.endswith(".ftl") and message.chat.type == 'private':
       try:
           file_info = await bot.get_file(message.document.file_id)
           downloaded_file = await bot.download_file(file_info.file_path)

           async with aiofiles.open(f'{prefix_folder}locales/ru.ftl', 'r', encoding='utf-8') as file:
               data = await file.read()

           async with aiofiles.open(f'{prefix_folder}locales/last_ru.ftl', 'w') as new_file:
               await new_file.write(data)

           async with aiofiles.open(f'{prefix_folder}locales/ru.ftl', 'wb') as new_file:
               await new_file.write(downloaded_file)
           await bot.send_message(message.chat.id, "Разметка успешно обновлена.")
           translator_create_or_update()
           await state.delete()

       except Exception as e:
           await bot.send_message(message.chat.id, f"Ошибка при обработке файла: {str(e)}")
   else:
       await bot.send_message(message.chat.id, "Пожалуйста, загрузите файл ftl.")

@bot.message_handler(state=AdminStates.spam, content_types=telebot.util.content_type_media, func=lambda message: message.chat.type == "private" and message.chat.id in ADMINS)
async def spam(message, state: StateContext, album=None, db=None):
    reply_message_id = None
    try:
        all_users = await db.get_all_users()
        count_people = 0

        if album:
            count_photos = len(album)
            media = []
            for i in album:
                if (i.photo):
                    media.append(
                        InputMediaPhoto(media=i.photo[-1].file_id, caption=i.caption, caption_entities=i.caption_entities, has_spoiler=i.has_media_spoiler))
                elif (i.video):
                    media.append(
                        InputMediaVideo(media=i.video.file_id, caption=i.caption, caption_entities=i.caption_entities, has_spoiler=i.has_media_spoiler))
                elif (i.document):
                    media.append(InputMediaDocument(media=i.document.file_id, caption=i.caption,
                                                    caption_entities=i.caption_entities))
            for i in all_users:
                try:
                    await bot.send_media_group(chat_id=i.chat_id, media=media, reply_to_message_id=reply_message_id)
                    count_people+=1
                except:
                    pass
            await bot.send_message(message.chat.id, f"Количество человек получившее рассылку: {count_people} ")
            await state.delete()
        else:
            for i in all_users:
                try:
                    await bot.copy_message(chat_id=i.chat_id, from_chat_id=message.chat.id, message_id=message.message_id,
                                       reply_to_message_id=reply_message_id)
                    count_people += 1
                except:
                    pass
            await bot.send_message(message.chat.id, f"Количество человек получившее рассылку: {count_people}")
            await state.delete()
    except Exception as e:
        if "Too Many Requests" in str(e):
            await bot.reply_to(message,
                               "Ваше сообщение не было доставлено, так как Telegram посчитал его спамом. Попробуйте отправить его еще раз.")
        elif "message to be replied not found" in str(e):
            await bot.reply_to(message,
                               "Ваше сообщение не было доставлено, так как мы не смогли найти оригинальное сообщение. Возможно, оно было удалено, являлось рассылкой, сообщением бота или недавно произошло обновление и старые сообщения больше не функциональны. Попробуйте отправить его еще раз без ответа на это сообщение или ответить на соседнее сообщение.")
        elif "chat not found" in str(e):
            pass
        else:
            tb = traceback.extract_tb(e.__traceback__)
            last_trace = tb[-1]
            line_number = last_trace.lineno
            line_content = last_trace.line
            await bot.send_message(DEVELOPER_ID,
                                   f"Ошибка при отправке сообщения от посредника в теме ({message.message_thread_id}) строка {line_number}: {line_content} код ошибки: {e}")


@bot.message_handler(state=AdminStates.upload_data, content_types=['document'])
async def handle_document(message, state: StateContext):
   if message.chat.id in ADMINS and message.document.mime_type == 'text/plain' and message.chat.type == 'private':
       try:
           file_info = await bot.get_file(message.document.file_id)
           downloaded_file = await bot.download_file(file_info.file_path)

           async with aiofiles.open('uploaded_user_topics.txt', 'wb') as new_file:
               await new_file.write(downloaded_file)

           async with aiofiles.open('uploaded_user_topics.txt', 'r', encoding='utf-8') as file:
               data = await file.read()

           lines = data.strip().split('\n')[1:]
           data = '\n'.join(lines)

           df = await asyncio.to_thread(pd.read_csv, StringIO(data), delimiter=' ',
                                      names=['chat_id', 'topic_id', 'user_name'])
           df = df.drop_duplicates(subset=['chat_id', 'topic_id'])

           async with aiosqlite.connect(db_path) as db:
               await db.execute('DELETE FROM users')
               await db.executemany('INSERT INTO users (chat_id, topic_id, user_name) VALUES (?, ?, ?)',
                                  df.values)
               await db.commit()

           await bot.send_message(message.chat.id, "Данные успешно загружены.")
           await state.delete()

       except Exception as e:
           await bot.send_message(message.chat.id, f"Ошибка при обработке файла: {str(e)}")
   else:
       await bot.send_message(message.chat.id, "Пожалуйста, загрузите файл TXT.")
