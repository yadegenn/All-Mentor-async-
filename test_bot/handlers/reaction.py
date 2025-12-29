import io
import traceback

from ..loader import bot, GROUP_ID, DEVELOPER_ID


@bot.message_reaction_handler(func=lambda message: True)
async def get_reactions(message, album: list = None, db=None):
    try:
        if message.chat.type == 'private':
            topic_message_id = await db.get_group_message_id_by_private_message(message.message_id)
            await bot.set_message_reaction(chat_id=GROUP_ID, message_id=topic_message_id,
                                     reaction=message.new_reaction)
        elif message.chat.id == int(GROUP_ID):
            chat_id = await db.get_chat_id_by_topic_id()
            private_message_id = await db.get_private_message_id_by_group_message(message.message_id)
            await bot.set_message_reaction(chat_id=chat_id, message_id=private_message_id,
                                           reaction=message.new_reaction)
    except Exception as e:

        if "message to react not found" in str(e):
            await bot.reply_to(message,
                               "Ваша реакция не была поставлена, так как мы не смогли получить оригинальное сообщение. Возможно, оно было удалено, являлось рассылкой, сообщением бота  или недавно произошло обновление и старые сообщения больше не функциональны. Попробуйте поставить реакцию на соседнее сообщение или сообщить об ошибке если все условия были соблюдены.")
        elif "'MessageReactionUpdated' object has no attribute 'message_thread_id'" in str(e):
            await bot.reply_to(message,
                               "Ваша реакция не была поставлена, так как мы не смогли получить оригинальное сообщение. Скорее всего вы поставили реакцию на сообщение бота. Попробуйте поставить реакцию на соседнее сообщение или сообщить об ошибке если все условия были соблюдены.")
        else:
            error_message = traceback.format_exc()
            error_file = io.BytesIO(error_message.encode('utf-8'))
            error_file.name = "error_log.txt"
            error_file.seek(0)
            await bot.send_document(chat_id=DEVELOPER_ID, document=error_file,
                                    caption=f"Ошибка при установлении эмоции  {message.from_user.username or message.from_user.first_name} (chat_id: {message.chat.id}, message_id: {message.message_id})")
