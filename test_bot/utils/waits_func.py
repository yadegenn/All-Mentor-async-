import os
import shutil
from datetime import datetime

from .translator import _
from ..loader import bot, prefix_folder


async def weekday_personal(message):
    now = datetime.now()
    weekday = now.weekday()
    await bot.reply_to(message,_(f"weekday_{weekday}_reminder_text"), parse_mode="HTML")

async def scheduled_reminder(chat_id):
    await bot.send_message(chat_id, _("sheduled_text"), parse_mode="HTML")

async def clean_log():
    error_log_dir = f"{prefix_folder}logs/errors"
    debug_log_dir = f"{prefix_folder}logs/debug"
    if os.path.exists(error_log_dir):
        shutil.rmtree(error_log_dir)
    if os.path.exists(debug_log_dir):
        shutil.rmtree(debug_log_dir)