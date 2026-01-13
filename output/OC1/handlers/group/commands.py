from datetime import datetime

import pytz
from ...middlewares.silent import silent_users
from ...utils.io import save_silent_users
from ...loader import bot, is_parasite
group_func = lambda message: message.chat.type == "supergroup" and not is_parasite

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
            if(str(i)==str(message.message_thread_id)):
                item = i
        if(item!=None):
            silent_users.discard(item)
            await bot.reply_to(message, "Тихий режим деактивирован")
        else:
            silent_users.add(user_data.topic_id)
            await bot.reply_to(message, "Тихий режим активирован")
    else:
        silent_users.add(user_data.topic_id)
        await bot.reply_to(message, "Тихий режим активирован")
    await save_silent_users(silent_users)


@bot.message_handler(commands=['info', 'i'], func=group_func )
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

