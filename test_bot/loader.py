from datetime import timedelta
from pathlib import Path
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
GROUP_ID = -1002365612235
prefix_folder = "test_bot/"
db_path = f"{prefix_folder}bot.db"
WORK_CHAT_FILE = f'{prefix_folder}work_chat.txt'
DEVELOPER_ID = 5434361630
ADMINS = [5434361630,6929772573]
is_weekend_have = False
is_latehour_have = True
is_photo_start = True
is_parasite = False
weekend = False
latehour = False
send_weekend_users = []
send_latehour_users = []
conflicted_commands = ['/calc','/card','/crypto',"/info","/silent",'/ban']
JSON_PATH = Path(f"{prefix_folder}currency_rate.json")
TOKEN = '6393711599:AAEonGZOT0-YA8wORN2SDyXLPCUfPYhanrU'
state_storage = StateMemoryStorage()
bot = AsyncTeleBot(TOKEN, state_storage=state_storage)


