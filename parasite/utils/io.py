import os

import aiofiles

from test_bot.loader import WORK_CHAT_FILE


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