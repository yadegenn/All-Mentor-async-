from datetime import datetime

from .translator import _
from ..loader import bot


async def weekday_personal(message):
    now = datetime.now()
    weekday = now.weekday()
    await bot.reply_to(message,_(f"weekday_{weekday}_reminder_text"), parse_mode="HTML")

async def scheduled_reminder(chat_id):
    await bot.send_message(chat_id, _("sheduled_text"), parse_mode="HTML")