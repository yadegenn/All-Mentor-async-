import io
import traceback
from pydoc import html

import telebot
from telebot.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
from ...loader import bot, GROUP_ID, DEVELOPER_ID
from ...utils.formats import caption_messages, text_message_format
from ...utils.markup_sources import get_content_data


@bot.message_handler(content_types=telebot.util.content_type_media, func=lambda message: message.chat.type == "private" )
async def private_messages(message, album: list = None, db=None, new_topic_id=None):
    # global weekend, latehour, send_weekend_users, send_latehour_users
    func = None
    attempt = {}


    try:
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

        else:
            error_message = traceback.format_exc()
            error_file = io.BytesIO(error_message.encode('utf-8'))
            error_file.name = "error_log.txt"
            error_file.seek(0)
            await bot.send_document(chat_id=DEVELOPER_ID,document=error_file,caption=f"Ошибка при отправке сообщения от пользователя  {message.from_user.username or message.from_user.first_name} ({message.chat.id})")

