import traceback
from pydoc import html

import telebot
from telebot.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio

from handlers.group.commands import work_chats
from loader import bot, GROUP_ID, DEVELOPER_ID
from utils.formats import caption_messages, text_message_format
from utils.markup_sources import get_content_data
from utils.math_and_types import check_conflicted_commands


@bot.message_handler(content_types=telebot.util.content_type_media, func=lambda message: message.chat.id == GROUP_ID and message.message_thread_id not in work_chats and message.message_thread_id!=None )
async def group_messages(message, album: list = None, db=None):
    reply_message_id = None
    try:
        chat_id = await db.get_chat_id_by_topic_id()
        if 'reply_to_message' in message.json and 'forum_topic_created' in message.json['reply_to_message']:
            pass
        else:
            reply_message_id = await db.get_private_message_id_by_group_message(int(message.json['reply_to_message']['message_id']))
        if album:
            count_photos = len(album)
            media = []
            for i in album:
                if (i.photo):
                    media.append(InputMediaPhoto(media=i.photo[-1].file_id, caption=i.caption, caption_entities=i.caption_entities, has_spoiler=i.has_media_spoiler))
                elif(i.video):
                    media.append(InputMediaVideo(media=i.video.file_id, caption=i.caption, caption_entities=i.caption_entities, has_spoiler=i.has_media_spoiler))
                elif (i.document):
                    media.append(InputMediaDocument(media=i.document.file_id, caption=i.caption, caption_entities=i.caption_entities))
                elif (i.audio):
                    media.append(InputMediaAudio(media=i.audio.file_id, caption=i.caption,
                                                    caption_entities=i.caption_entities))
            await db.add_message_to_db(await bot.send_media_group(chat_id=chat_id,media=media, reply_to_message_id=reply_message_id), message.message_thread_id, album)
        else:
            if(check_conflicted_commands(message.text)):
                pass
            else:
                await db.add_message_to_db(
                    await bot.copy_message(chat_id=chat_id, from_chat_id=message.chat.id, message_id=message.message_id,
                                           reply_to_message_id=reply_message_id), message.message_thread_id, None)
    except Exception as e:
        if "Too Many Requests" in str(e):
            await bot.reply_to(message,
                               "Ваше сообщение не было доставлено, так как Telegram посчитал его спамом. Попробуйте отправить его еще раз.")
        elif "message to be replied not found" in str(e):
            await bot.reply_to(message,
                               "Ваше сообщение не было доставлено, так как мы не смогли найти оригинальное сообщение. Возможно, оно было удалено, являлось рассылкой, сообщением бота или недавно произошло обновление и старые сообщения больше не функциональны. Попробуйте отправить его еще раз без ответа на это сообщение или ответить на соседнее сообщение.")
        elif "chat not found" in str(e):
            pass
        elif "bot was blocked by the user" in str(e):
            await bot.reply_to(message, "Ваше сообщение не было доставлено, пользователь заблокировал бота")
        else:
            tb = traceback.extract_tb(e.__traceback__)
            last_trace = tb[-1]
            line_number = last_trace.lineno
            line_content = last_trace.line
            await bot.send_message(DEVELOPER_ID,
                                   f"Ошибка при отправке сообщения от посредника в теме ({message.message_thread_id}) строка {line_number}: {line_content} код ошибки: {e}")