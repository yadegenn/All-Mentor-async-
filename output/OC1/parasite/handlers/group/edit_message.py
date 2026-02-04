import io
import traceback

import telebot

from ...loader import GROUP_ID, bot, DEVELOPER_ID
from ...utils.markup_sources import get_content_data

group_func=lambda message: message.chat.id == int(GROUP_ID)

@bot.edited_message_handler(content_types=telebot.util.content_type_media, func=group_func)
async def edited_message(message, db=None):
    try:
        content_data = get_content_data(message)
        chat_id = await db.get_chat_id_by_topic_id()
        private_message_id = await db.get_private_message_id_by_group_message(message.message_id)
        if message.content_type + "_caption_edit" in content_data:

            data = content_data[message.content_type]
            try:
                await bot.edit_message_caption(
                    chat_id=chat_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    message_id=private_message_id
                )
            except Exception as e:
                if "specified new message content and reply markup are exactly the same as a current content and reply markup of the message" in str(
                        e) and message.media_group_id:
                    await bot.reply_to(message, "Бот пока не поддерживает изменение медиа в альбоме")
            if (data["file_id"] and message.media_group_id and message.caption == None):
                await bot.reply_to(message, "Бот пока не поддерживает изменение медиа в альбоме")
            elif (data["file_id"] and message.media_group_id == None):
                await bot.edit_message_media(
                    chat_id=chat_id,
                    media=data["object"](data["file_id"], caption=message.caption,
                                         caption_entities=message.caption_entities),
                    message_id=private_message_id
                )
        elif (message.content_type == "text"):
            await bot.edit_message_text(chat_id=chat_id, message_id=private_message_id, text=message.text,
                                        entities=message.entities)
        else:
            # редактирование всего остального
            pass
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
            error_message = traceback.format_exc()
            error_file = io.BytesIO(error_message.encode('utf-8'))
            error_file.name = "error_log.txt"
            error_file.seek(0)
            await bot.send_document(chat_id=DEVELOPER_ID, document=error_file,
                                    caption=f"Ошибка при редактировании сообщения от пользователя  {message.from_user.username or message.from_user.first_name} (chat_id: {message.chat.id}, message_id: {message.message_id})")