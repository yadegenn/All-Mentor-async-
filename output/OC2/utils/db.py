from dataclasses import dataclass
from datetime import datetime
from typing import List
from ..loader import pool
import psycopg

@dataclass
class week_period_class:
    chat_id: int
    date: datetime

async def init_db():
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS week_period (
                    chat_id BIGINT,
                    date TIMESTAMPTZ,
                    PRIMARY KEY (chat_id)
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    chat_id BIGINT,
                    topic_id BIGINT,
                    nickname TEXT,
                    username TEXT,
                    is_ban INTEGER DEFAULT 0,
                    reg_date TIMESTAMPTZ,
                    PRIMARY KEY (chat_id, topic_id)
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS group_messages (
                    topic_id BIGINT,
                    message_id BIGINT,
                    local_id BIGINT,
                    PRIMARY KEY (topic_id, local_id)
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS private_messages (
                    chat_id BIGINT,
                    message_id BIGINT,
                    local_id BIGINT,
                    PRIMARY KEY (chat_id, local_id)
                )
            ''')



async def get_all_user_week_period() -> List[week_period_class]:
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT chat_id, date FROM week_period')
            rows = await cur.fetchall()

            return [week_period_class(chat_id, date) for chat_id, date in rows]
async def add_user_week_period(chat_id: int | str, date: datetime):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
                INSERT INTO week_period (chat_id, date)
                VALUES (%s, %s)
            ''', (chat_id, date))


async def delete_user_week_period(chat_id: int | str):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute('DELETE FROM week_period WHERE chat_id=%s', (chat_id,))
