import asyncio
import time
from collections import deque
# TEST
from datetime import timedelta

from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telebot.states.asyncio.middleware import StateMiddleware
from telebot import asyncio_filters

from .handlers.private.messages import GlobalQueueManager, manager
from .middlewares.spam_control import RateLimitMiddleware
from .middlewares.album import AlbumMiddleware
from .middlewares.ban import BanMiddleware
from .middlewares.db import DatabaseMiddleware
from .middlewares.silent import SilentMiddleware
from .middlewares.timeout import UserTimeChecker, init_checker
# from quart_cors import cors
# убираем ipv6
from .utils.calc import update_rates
from .utils.checker import checker
from .utils.db import init_db, get_all_user_week_period
from .loader import bot, GROUP_ID, db_str, pool
from .utils.disable_ipv6 import disable_ipv6
from .utils.logging import setup_logging
from .utils.translator import _
from . import handlers
import psycopg
from psycopg_pool import AsyncConnectionPool



disable_ipv6()

# данные
scheduler = AsyncIOScheduler()

async def days_ping(chat_id):
    await bot.send_message(chat_id, "Здравствуйте, чем могу помочь?")






scheduler.add_job(checker, "interval", seconds=5)
scheduler.add_job(update_rates, "cron", hour=17,minute=0,timezone=ZoneInfo("Europe/Moscow"))
# Запуск бота
async def main():
    global db_path
    print("Бот запущен!")
    setup_logging()
    await pool.open()
    db_object = await init_db()

    bot.add_custom_filter(asyncio_filters.StateFilter(bot))
    # bot.setup_middleware(RateLimitMiddleware(limit_messages=5,limit_albums=3,time_window=40, bot=bot))
    bot.setup_middleware(StateMiddleware(bot))
    bot.setup_middleware(AlbumMiddleware())
    bot.setup_middleware(UserTimeChecker(GROUP_ID))
    bot.setup_middleware(DatabaseMiddleware(bot, GROUP_ID))
    bot.setup_middleware(BanMiddleware(bot, GROUP_ID))
    bot.setup_middleware(SilentMiddleware())
    worker_task = asyncio.create_task(manager.start_worker())
    await init_checker()
    while True:
        try:
            if worker_task.done():
                worker_task = asyncio.create_task(manager.start_worker())
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
            await pool.close()
            worker_task.cancel()
            if scheduler.running:
                scheduler.shutdown()




if __name__ == "__main__":
    asyncio.run(main())
