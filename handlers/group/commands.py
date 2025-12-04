from datetime import datetime

import pytz

from loader import bot, ADMINS
from utils.io import load_work_chats, save_work_chats

group_func = lambda message: message.chat.type == "supergroup"

@bot.message_handler(commands=['ban'], func=group_func)
async def ban_user(message, db=None):
    await bot.reply_to(message, await db.update_ban_status_by_topic_id())

@bot.message_handler(commands=['silent'], func=group_func)
async def silent(message, db=None):
    global silent_users
    user_data = await db.get_user_by_topic_id()

    if(len(silent_users)>0):
        item = None
        for i in silent_users:
            if(str(i.topic_id)==str(message.message_thread_id)):
                item = i
        if(item!=None):
            silent_users.remove(item)
            await bot.reply_to(message, "Тихий режим деактивирован")
        else:
            silent_users.append(user_data)
            await bot.reply_to(message, "Тихий режим активирован")
    else:
        silent_users.append(user_data)
        await bot.reply_to(message, "Тихий режим активирован")

@bot.message_handler(commands=['info', 'i'], func=group_func)
async def information_group(message, db=None):
    user_data = await db.get_user_by_topic_id()
    reg_data = datetime.strptime(user_data.reg_date, '%Y-%m-%d %H:%M:%S.%f')
    utc_zone = pytz.utc
    dt_aware_utc = utc_zone.localize(reg_data)
    moscow_zone = pytz.timezone('Europe/Moscow')
    dt_moscow = dt_aware_utc.astimezone(moscow_zone)
    formatted_output = dt_moscow.strftime('%Y-%m-%d %H:%M:%S') + ' UTC+03:00'
    chat_info = await bot.get_chat(user_data.chat_id)

    await bot.reply_to(message, f"Username: <a href='tg://user?id={user_data.chat_id}'>@{chat_info.username}</a>\nNickname: {user_data.nickname}\nID: {user_data.chat_id}\nЗаблокирован: {'False' if user_data.is_ban==0 else 'True'}\nДата регистрации:\n{formatted_output}",parse_mode='HTML')

work_chats = load_work_chats()
@bot.message_handler(commands=['remove_work_chat'], func=group_func)
async def handle_remove_work_chat(message):
    if message.chat.id in ADMINS:
        args = message.text.split()
        if len(args) != 2:
            await bot.reply_to(message, "Usage: /remove_work_chat <topic_id>")
            return
        try:
            topic_id = int(args[1])
            if topic_id in work_chats:
                work_chats.remove(topic_id)
                await save_work_chats(work_chats)
                await bot.reply_to(message, f"Topic ID {topic_id} removed from work chats.")
            else:
                await bot.reply_to(message, f"Topic ID {topic_id} is not in the work chats list.")
        except ValueError:
            await bot.reply_to(message, "Invalid topic ID. Please provide a valid integer.")
    else:
        await bot.reply_to(message, "You don't have permission to use this command.")
@bot.message_handler(commands=['add_work_chat'], func=group_func)
async def handle_add_work_chat(message):
    if message.chat.id in ADMINS:
        args = message.text.split()
        if len(args) != 2:
            await bot.reply_to(message, "Usage: /add_work_chat <topic_id>")
            return
        try:
            topic_id = int(args[1])
            work_chats.add(topic_id)
            await save_work_chats(work_chats)
            await bot.reply_to(message, f"Topic ID {topic_id} added to work chats.")
        except ValueError:
            await bot.reply_to(message, "Invalid topic ID. Please provide a valid integer.")
    else:
        await bot.reply_to(message, "You don't have permission to use this command.")