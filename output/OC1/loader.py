from datetime import timedelta
from pathlib import Path
from psycopg_pool import AsyncConnectionPool
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
GROUP_ID = -1002520385279
TOKEN = '7388589430:AAH-tE2t_29qBrgWHNC8P1I-eFz_7W5c45w'
prefix = 'OC1'
prefix_folder = f"{prefix}/"
db_str = f"dbname={prefix} user=admin password=E-M_i-LGO0 host=5.129.223.183"
WORK_CHAT_FILE = f'{prefix_folder}work_chat.txt'
DEVELOPER_ID = 5434361630
ADMINS = [5434361630,6929772573]
# is_weekend_have = False
# is_latehour_have = True
# is_photo_start = True
is_parasite = False
is_weekday_period = True
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