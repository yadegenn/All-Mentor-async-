import aiosqlite


async def init_db(db_path):
    db_object = await aiosqlite.connect(db_path)
    await db_object.execute('PRAGMA foreign_keys = ON')
    await db_object.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER,
            topic_id INTEGER,
            nickname TEXT,
            username TEXT,
            is_ban INTEGER DEFAULT 0,
            reg_date DATETIME,
            PRIMARY KEY (chat_id, topic_id)
        )
    ''')
    await db_object.execute('''
        CREATE TABLE IF NOT EXISTS group_messages (
            topic_id INTEGER,
            message_id INTEGER,
            local_id INTEGER,
            PRIMARY KEY (topic_id, local_id)
        )
    ''')
    await db_object.execute('''
        CREATE TABLE IF NOT EXISTS private_messages (
            chat_id INTEGER,
            message_id INTEGER,
            local_id INTEGER,
            PRIMARY KEY (chat_id, local_id)
        )
    ''')
    await db_object.commit()
    return db_object