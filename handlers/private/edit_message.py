import traceback

import telebot

from loader import bot, GROUP_ID, DEVELOPER_ID
from utils.formats import caption_messages, text_message_format
from utils.markup_sources import get_content_data

private_func=lambda message: message.chat.type == "private"

@bot.edited_message_handler(content_types=telebot.util.content_type_media, func=private_func)
async def edited_message(message, db=None):
    try:
        content_data = get_content_data(message)
        topic_message_id = await db.get_group_message_id_by_private_message(message.message_id)
        if message.content_type + "_caption_edit" in content_data:
            data = content_data[message.content_type + "_caption_edit"]
            result_text, result_entities = caption_messages(message, True)

            # Вызываем соответствующую функцию
            try:
                await bot.edit_message_caption(
                    chat_id=GROUP_ID,
                    caption=result_text if message.caption is not None else (
                        "" if data["show_sender_details"] == False else result_text),
                    caption_entities=result_entities if message.caption is not None else (
                        None if data["show_sender_details"] == False else result_entities),
                    message_id=topic_message_id
                )
            except Exception as e:
                if "specified new message content and reply markup are exactly the same as a current content and reply markup of the message" in str(
                        e) and message.media_group_id:
                    await bot.reply_to(message, "Бот пока не поддерживает изменение медиа в альбоме")
            # if(data["file_id"] and message.media_group_id and message.caption == None):
            #     print(message)
            #     await bot.reply_to(message, "Бот пока не поддерживает изменение медиа в альбоме")
            if (data["file_id"] and message.media_group_id == None):
                await bot.edit_message_media(
                    chat_id=GROUP_ID,
                    media=content_data[message.content_type]["object"](data["file_id"], caption=result_text,
                                                                       caption_entities=result_entities),
                    message_id=topic_message_id
                )
        elif (message.content_type == "text"):
            result_text, result_entities = text_message_format(message, True)
            await bot.edit_message_text(chat_id=GROUP_ID, message_id=topic_message_id, text=result_text,
                                        entities=result_entities)
        else:
            print(message.content_type)
    except Exception as e:
        if "message to edit not found" in str(e):
            if(message.chat.type == 'private'):
                await bot.reply_to(message,
                                   "Ваше сообщение не было отредактировано, так как мы не смогли получить оригинальное сообщение. Возможно, оно было удалено посредником, не успело отправиться или недавно произошло обновление и старые сообщения больше не функциональны. Попробуйте отредактировать это сообщение снова или отредактировать соседнее сообщение. Если все условия были соблюдены и ошибка повторяется, сообщите о ней.")
            elif message.chat.id == int(GROUP_ID):
                await bot.reply_to(message,
                                   "Ваше сообщение не было отредактировано, так как мы не смогли получить оригинальное сообщение. Возможно, оно было удалено пользователем, не успело отправиться или недавно произошло обновление и старые сообщения больше не функциональны. Попробуйте отредактировать это сообщение снова или отредактировать соседнее сообщение. Если все условия были соблюдены и ошибка повторяется, сообщите о ней.")
        elif "specified new message content and reply markup are exactly the same as a current content and reply markup of the message" in str(e):
            pass
        else:
            tb = traceback.extract_tb(e.__traceback__)
            last_trace = tb[-1]
            line_number = last_trace.lineno
            line_content = last_trace.line
            mess = "чате с пользователем" if message.chat.id else "группе"
            await bot.send_message(DEVELOPER_ID,
                                   f"Ошибка при редактировании сообщения в {mess} ({message.message_id}) строка {line_number}: {line_content} код ошибки: {e}")