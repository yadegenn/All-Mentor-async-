import asyncio
# TEST
from datetime import timedelta

from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telebot.states.asyncio.middleware import StateMiddleware
from telebot import asyncio_filters
from test_bot.middlewares.album import AlbumMiddleware
from test_bot.middlewares.ban import BanMiddleware
from test_bot.middlewares.db import DatabaseMiddleware
from test_bot.middlewares.silent import SilentMiddleware
from test_bot.middlewares.timeout import UserTimeChecker
# from quart_cors import cors
# убираем ipv6
from utils.calc import update_rates
from utils.checker import checker
from utils.db import init_db
from loader import bot, GROUP_ID, \
    is_weekend_have, is_latehour_have
from utils.disable_ipv6 import disable_ipv6
from utils.logging import setup_logging
from utils.translator import _

disable_ipv6()

# данные
scheduler = AsyncIOScheduler()

async def days_ping(chat_id):
    await bot.send_message(chat_id, "Здравствуйте, чем могу помочь?")
async def scheduled_reminder(chat_id):
    await bot.send_message(chat_id, _("sheduled_text"), parse_mode="HTML")


rules_checker = [
    {"type": "private",
     "timeout": timedelta(seconds=int(_("sheduled_time")) if _("sheduled_time").isdigit() else 0),
     "action": scheduled_reminder}
]
rules_checker.append({"type": "weekend", "day": 5} if is_weekend_have else {"type": "none"})
rules_checker.append({"type": "weekend", "day": 6} if is_weekend_have else {"type": "none"})
rules_checker.append({"type": "latehour", "hour": 19} if is_latehour_have else {"type": "none"})


scheduler.add_job(checker, "interval", seconds=5)
scheduler.add_job(update_rates, "cron", hour=17,minute=0,timezone=ZoneInfo("Europe/Moscow"))
# Запуск бота
async def main():
    global db_path
    print("Бот запущен!")
    setup_logging()
    db_object = await init_db(db_path)

    bot.add_custom_filter(asyncio_filters.StateFilter(bot))
    # bot.setup_middleware(RateLimitMiddleware(limit_messages=5,limit_albums=3,time_window=40, bot=bot))
    bot.setup_middleware(StateMiddleware(bot))
    bot.setup_middleware(UserTimeChecker(GROUP_ID, db_path))
    bot.setup_middleware(DatabaseMiddleware(db_object, bot, GROUP_ID))
    bot.setup_middleware(BanMiddleware(db_object, bot, GROUP_ID))
    bot.setup_middleware(AlbumMiddleware())
    bot.setup_middleware(SilentMiddleware())

    while True:
        try:
            if scheduler.running == False:
                scheduler.start()
            await bot.infinity_polling(allowed_updates=[
                'message',
                'edited_message',
                'channel_post',
                'edited_channel_post',
                'message_reaction',
                'message_reaction_count',
                'callback_query',
                'chat_member'
            ])
        except Exception as e:
            await db_object.close()
            if scheduler.running:
                scheduler.shutdown()




if __name__ == "__main__":
    asyncio.run(main())
