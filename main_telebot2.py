import asyncio
# TEST
import copy
import html
import inspect
import json
import logging
import traceback
from datetime import timedelta, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from io import StringIO
from pathlib import Path
from zoneinfo import ZoneInfo

import aiofiles
import aiosqlite
import pytz
import telebot
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pandas as pd
from telebot.asyncio_helper import ApiTelegramException
from telebot.states.asyncio.middleware import StateMiddleware
from telebot import asyncio_filters
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.states import StatesGroup, State
from telebot.states.asyncio import StateContext
from telebot.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument,  InlineKeyboardMarkup, \
    InlineKeyboardButton,  InputFile, InputMediaAudio, LinkPreviewOptions, \
    InputMediaAnimation
from telebot.types import MessageEntity
from middlewares.album import AlbumMiddleware
from middlewares.ban import BanMiddleware
from middlewares.db import DatabaseMiddleware
from middlewares.silent import SilentMiddleware
from middlewares.silent import silent_users
from loader import db_path,weekend,latehour,send_weekend_users,send_latehour_users,WORK_CHAT_FILE,state_storage
from middlewares.timeout import UserTimeChecker, user_data, group_data
from fluentogram import FluentTranslator, TranslatorHub
from fluent_compiler.bundle import FluentBundle
from quart import Quart, request, jsonify
# from quart_cors import cors
from hypercorn.asyncio import serve
from hypercorn.config import Config
# убираем ipv6
import socket
import handlers
from utils.calc import update_rates
from utils.checker import checker
from utils.db import init_db
from loader import bot, conflicted_commands, WORK_CHAT_FILE, ADMINS, prefix_folder, DEVELOPER_ID, GROUP_ID, \
    is_weekend_have, is_latehour_have
from utils.disable_ipv6 import disable_ipv6
from utils.logging import setup_logging
from utils.translator import _, translator_create_or_update

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
