from pathlib import Path

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
GROUP_ID = --1002365612235
prefix_folder = "../"
db_path = f"{prefix_folder}bot.db"
WORK_CHAT_FILE = f'{prefix_folder}work_chat.txt'
DEVELOPER_ID = 5434361630
ADMINS = [5434361630,6929772573]
is_weekend_have = False
is_latehour_have = True
is_photo_start = True
is_parasite = True
weekend = False
latehour = False
send_weekend_users = []
send_latehour_users = []
conflicted_commands = ['/calc','/card','/crypto',"/info","/silent"]
JSON_PATH = Path("currency_rate.json")
TOKEN = '8501698016:AAFxlwN5zYS1wefShLDC-mfx3EZQO8sSfwY'
state_storage = StateMemoryStorage()
bot = AsyncTeleBot(TOKEN, state_storage=state_storage)