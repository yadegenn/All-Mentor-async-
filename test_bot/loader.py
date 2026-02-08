from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import os
from psycopg_pool import AsyncConnectionPool
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
load_dotenv()
GROUP_ID = os.getenv("TEST_BOT_GROUP_ID")
TOKEN = os.getenv("TEST_BOT_API")
prefix = "test_bot"
prefix_folder = f"{prefix}/"
db_str = f"dbname={prefix} user={os.getenv("db_user")} password={os.getenv("db_password")} host={os.getenv("db_ip")}"
WORK_CHAT_FILE = f'{prefix_folder}work_chat.txt'
DEVELOPER_ID = os.getenv("DEVELOPER_ID")
ADMINS = [int(admin) for admin in os.getenv("ADMINS").split(",")]
# is_weekend_have = False
# is_latehour_have = True
# is_photo_start = True
is_parasite = False
is_weekday_period = True
is_menu_show = False
is_scheduled_message = True
# weekend = False
# latehour = False
send_weekend_users = []
send_latehour_users = []
conflicted_commands = ['/calc','/card','/crypto',"/info","/silent",'/ban']
JSON_PATH = Path(f"{prefix_folder}currency_rate.json")
state_storage = StateMemoryStorage()
bot = AsyncTeleBot(TOKEN, state_storage=state_storage)


pool = AsyncConnectionPool(
    conninfo=db_str,
    min_size=1,
    max_size=3,
    open=False
)