import os

import aiofiles

from ..loader import WORK_CHAT_FILE, prefix_folder


# загрузка текстового документа с id чатов где бот не будет ругаться на то что чат недействителен
def load_work_chats():
    if os.path.exists(WORK_CHAT_FILE):
        with open(WORK_CHAT_FILE, 'r') as f:
            return set(int(line.strip()) for line in f)
    return set()

# сохранение текстового документа с id чатов где бот не будет ругаться на то что чат недействителен
async def save_work_chats(work_chats):
    try:
        async with aiofiles.open(WORK_CHAT_FILE, 'w') as f:
            await f.write('\n'.join(str(chat_id) for chat_id in work_chats))
    except Exception as e:
        print(f"Error saving work chats: {e}")

async def load_silent_user():
    if os.path.exists(f'{prefix_folder}silent_users.txt'):
        async with aiofiles.open(f'{prefix_folder}silent_users.txt', mode='r') as f:
            lines = await f.readlines()
            return {int(line.strip()) for line in lines}
    return set()

# сохранение текстового документа с id чатов где бот не будет ругаться на то что чат недействителен
async def save_silent_users(silent_users: list):
    try:
        async with aiofiles.open(f'{prefix_folder}silent_users.txt', 'w') as f:
            await f.write('\n'.join(str(chat_id) for chat_id in silent_users))
    except Exception as e:
        print(f"Error saving work chats: {e}")