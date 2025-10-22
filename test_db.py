import asyncio
import pytest
import aiosqlite
import html
from unittest.mock import AsyncMock, MagicMock

# Импортируем тестируемый класс
from middlewares.db import Database

# Импорты, необходимые для моков и тестов
from telebot.types import Message, User, Chat, ForumTopic, MessageID

# Определяем константы для тестов
GROUP_ID = -1001234567890
USER_ID = 12345
USER_NAME = "testuser"
FIRST_NAME = "Test"
TOPIC_ID = 54321

# Помечаем все тесты в этом файле как асинхронные
pytestmark = pytest.mark.asyncio

# --- ФИКСТУРЫ (Настройка тестовой среды) ---

@pytest.fixture
def in_memory_db(event_loop):
    """Фикстура для создания и инициализации базы данных в памяти."""
    db_connection = None
    async def setup_db():
        db = await aiosqlite.connect(":memory:")
        await db.execute('PRAGMA foreign_keys = ON')
        await db.execute('CREATE TABLE users (chat_id INTEGER, topic_id INTEGER, user_name TEXT, PRIMARY KEY (chat_id, topic_id))')
        await db.execute('CREATE TABLE group_messages (topic_id INTEGER, message_id INTEGER, local_id INTEGER, PRIMARY KEY (topic_id, local_id))')
        await db.execute('CREATE TABLE private_messages (chat_id INTEGER, message_id INTEGER, local_id INTEGER, PRIMARY KEY (chat_id, local_id))')
        await db.commit()
        return db
    db_connection = event_loop.run_until_complete(setup_db())
    yield db_connection
    event_loop.run_until_complete(db_connection.close())

@pytest.fixture
def mock_bot():
    """Фикстура для создания мок-объекта бота."""
    bot = AsyncMock()
    bot.create_forum_topic.return_value = ForumTopic(message_thread_id=TOPIC_ID, name=USER_NAME, icon_color=0)
    return bot

@pytest.fixture
def mock_private_message():
    """Фикстура для создания мок-объекта сообщения от пользователя в ЛС."""
    message = MagicMock(spec=Message)
    message.from_user = User(id=USER_ID, is_bot=False, first_name=FIRST_NAME, username=USER_NAME)
    message.chat = Chat(id=USER_ID, type='private')
    message.chat.id = USER_ID
    # Убираем message_thread_id для личных сообщений
    message.message_thread_id = None
    return message

@pytest.fixture
def mock_group_message():
    """Фикстура для создания мок-объекта сообщения из группы."""
    message = MagicMock(spec=Message)
    message.from_user = User(id=98765, is_bot=False, first_name="Admin", username="admin_user")
    message.chat = Chat(id=GROUP_ID, type='supergroup')
    message.chat.id = GROUP_ID
    # Добавляем message_thread_id для сообщений из темы
    message.message_thread_id = TOPIC_ID
    return message


# --- ТЕСТЫ ЛОГИКИ СОЗДАНИЯ/ПОЛУЧЕНИЯ ТЕМ ---

async def test_get_or_create_topic_for_new_user(in_memory_db, mock_bot, mock_private_message):
    """Тест: Проверяет создание новой темы для нового пользователя."""
    db_instance = Database(in_memory_db, mock_bot, mock_private_message, GROUP_ID)
    topic_id = await db_instance.get_or_create_topic()
    assert topic_id == TOPIC_ID
    mock_bot.create_forum_topic.assert_called_once_with(GROUP_ID, html.escape(USER_NAME))
    async with in_memory_db.execute('SELECT topic_id, user_name FROM users WHERE chat_id = ?', (USER_ID,)) as cursor:
        result = await cursor.fetchone()
        assert result is not None
        assert result[0] == TOPIC_ID
        assert result[1] == html.escape(USER_NAME)

async def test_get_or_create_topic_for_existing_user(in_memory_db, mock_bot, mock_private_message):
    """Тест: Проверяет получение существующей темы для пользователя, который уже есть в БД."""
    await in_memory_db.execute('INSERT INTO users (chat_id, topic_id, user_name) VALUES (?, ?, ?)', (USER_ID, TOPIC_ID, USER_NAME))
    await in_memory_db.commit()
    db_instance = Database(in_memory_db, mock_bot, mock_private_message, GROUP_ID)
    topic_id = await db_instance.get_or_create_topic()
    assert topic_id == TOPIC_ID
    mock_bot.reopen_forum_topic.assert_called_once_with(GROUP_ID, TOPIC_ID)
    mock_bot.create_forum_topic.assert_not_called()

async def test_get_or_create_topic_when_topic_deleted_in_telegram(in_memory_db, mock_bot, mock_private_message):
    """Тест: Проверяет случай, когда тема есть в БД, но удалена в Telegram."""
    deleted_topic_id = 11111
    mock_bot.reopen_forum_topic.side_effect = Exception("TOPIC_ID_INVALID")
    await in_memory_db.execute('INSERT INTO users (chat_id, topic_id, user_name) VALUES (?, ?, ?)', (USER_ID, deleted_topic_id, USER_NAME))
    await in_memory_db.commit()
    db_instance = Database(in_memory_db, mock_bot, mock_private_message, GROUP_ID)
    new_topic_id = await db_instance.get_or_create_topic()
    assert new_topic_id == TOPIC_ID
    mock_bot.reopen_forum_topic.assert_called_once_with(GROUP_ID, deleted_topic_id)
    mock_bot.create_forum_topic.assert_called_once_with(GROUP_ID, html.escape(USER_NAME))

async def test_get_or_create_topic_handles_topic_not_modified_error(in_memory_db, mock_bot, mock_private_message):
    """НОВЫЙ ТЕСТ: Проверяет, что ошибка 'TOPIC_NOT_MODIFIED' обрабатывается как успех."""
    mock_bot.reopen_forum_topic.side_effect = Exception("TOPIC_NOT_MODIFIED")
    await in_memory_db.execute('INSERT INTO users (chat_id, topic_id, user_name) VALUES (?, ?, ?)', (USER_ID, TOPIC_ID, USER_NAME))
    await in_memory_db.commit()
    db_instance = Database(in_memory_db, mock_bot, mock_private_message, GROUP_ID)
    topic_id = await db_instance.get_or_create_topic()
    assert topic_id == TOPIC_ID
    mock_bot.create_forum_topic.assert_not_called()

async def test_username_is_properly_escaped(in_memory_db, mock_bot, mock_private_message):
    """НОВЫЙ ТЕСТ: Проверяет, что HTML-символы в имени пользователя экранируются."""
    bad_username = "<Hacker>"
    escaped_username = "&lt;Hacker&gt;"
    mock_private_message.from_user.username = bad_username
    db_instance = Database(in_memory_db, mock_bot, mock_private_message, GROUP_ID)
    await db_instance.get_or_create_topic()
    mock_bot.create_forum_topic.assert_called_once_with(GROUP_ID, escaped_username)

# --- ТЕСТЫ СОПОСТАВЛЕНИЯ И ДОБАВЛЕНИЯ СООБЩЕНИЙ ---

async def test_add_message_to_db_private_to_group(in_memory_db, mock_bot, mock_private_message):
    """Тест: Проверяет корректное сопоставление ID при отправке из личного чата в группу."""
    await in_memory_db.execute('INSERT INTO users (chat_id, topic_id, user_name) VALUES (?, ?, ?)', (USER_ID, TOPIC_ID, USER_NAME))
    await in_memory_db.commit()
    db_instance = Database(in_memory_db, mock_bot, mock_private_message, GROUP_ID)
    mock_private_message.message_id = 100
    new_group_message = MagicMock(spec=MessageID, message_id=200)
    await db_instance.add_message_to_db(new_group_message, TOPIC_ID, None)
    async with in_memory_db.execute('SELECT message_id FROM private_messages WHERE local_id = 1') as c:
        assert (await c.fetchone())[0] == 100
    async with in_memory_db.execute('SELECT message_id FROM group_messages WHERE local_id = 1') as c:
        assert (await c.fetchone())[0] == 200

async def test_add_message_to_db_group_to_private(in_memory_db, mock_bot, mock_group_message):
    """НОВЫЙ ТЕСТ: Проверяет корректное сопоставление ID при отправке из группы в личный чат."""
    await in_memory_db.execute('INSERT INTO users (chat_id, topic_id, user_name) VALUES (?, ?, ?)', (USER_ID, TOPIC_ID, USER_NAME))
    await in_memory_db.commit()
    db_instance = Database(in_memory_db, mock_bot, mock_group_message, GROUP_ID)
    mock_group_message.message_id = 300
    new_private_message = MagicMock(spec=MessageID, message_id=400)
    await db_instance.add_message_to_db(new_private_message, TOPIC_ID, None)
    async with in_memory_db.execute('SELECT message_id FROM group_messages WHERE local_id = 1') as c:
        assert (await c.fetchone())[0] == 300
    async with in_memory_db.execute('SELECT message_id FROM private_messages WHERE local_id = 1') as c:
        assert (await c.fetchone())[0] == 400

async def test_add_message_to_db_with_album(in_memory_db, mock_bot, mock_private_message):
    """НОВЫЙ ТЕСТ: Проверяет корректное сохранение альбома из нескольких сообщений."""
    await in_memory_db.execute('INSERT INTO users (chat_id, topic_id, user_name) VALUES (?, ?, ?)', (USER_ID, TOPIC_ID, USER_NAME))
    await in_memory_db.commit()
    db_instance = Database(in_memory_db, mock_bot, mock_private_message, GROUP_ID)
    album_from_user = [MagicMock(spec=Message, message_id=101), MagicMock(spec=Message, message_id=102)]
    sent_album_messages = [MagicMock(spec=MessageID, message_id=201), MagicMock(spec=MessageID, message_id=202)]
    # Имитируем, что `add_message_to_db` вызывается для первого сообщения альбома
    mock_private_message.message_id = album_from_user[0].message_id
    await db_instance.add_message_to_db(sent_album_messages, TOPIC_ID, album_from_user)
    async with in_memory_db.execute('SELECT message_id FROM private_messages ORDER BY message_id') as c:
        results = await c.fetchall()
        assert results == [(101,), (102,)]
    async with in_memory_db.execute('SELECT message_id FROM group_messages ORDER BY message_id') as c:
        results = await c.fetchall()
        assert results == [(201,), (202,)]

async def test_get_group_message_id_by_private_message(in_memory_db, mock_bot, mock_private_message):
    """Тест: Проверяет, что можно найти ID сообщения в группе по ID из личного чата."""
    await in_memory_db.execute('INSERT INTO users (chat_id, topic_id) VALUES (?, ?)', (USER_ID, TOPIC_ID))
    await in_memory_db.execute('INSERT INTO private_messages (chat_id, message_id, local_id) VALUES (?, ?, ?)', (USER_ID, 100, 1))
    await in_memory_db.execute('INSERT INTO group_messages (topic_id, message_id, local_id) VALUES (?, ?, ?)', (TOPIC_ID, 200, 1))
    await in_memory_db.commit()
    db_instance = Database(in_memory_db, mock_bot, mock_private_message, GROUP_ID)
    found_id = await db_instance.get_group_message_id_by_private_message(100)
    assert found_id == 200

async def test_get_private_message_id_by_group_message(in_memory_db, mock_bot, mock_group_message):
    """НОВЫЙ ТЕСТ: Проверяет, что можно найти ID сообщения в личке по ID из группы."""
    await in_memory_db.execute('INSERT INTO users (chat_id, topic_id) VALUES (?, ?)', (USER_ID, TOPIC_ID))
    await in_memory_db.execute('INSERT INTO private_messages (chat_id, message_id, local_id) VALUES (?, ?, ?)', (USER_ID, 100, 1))
    await in_memory_db.execute('INSERT INTO group_messages (topic_id, message_id, local_id) VALUES (?, ?, ?)', (TOPIC_ID, 200, 1))
    await in_memory_db.commit()
    db_instance = Database(in_memory_db, mock_bot, mock_group_message, GROUP_ID)
    found_id = await db_instance.get_private_message_id_by_group_message(200)
    assert found_id == 100

async def test_message_id_mapping_returns_none_for_nonexistent_message(in_memory_db, mock_bot, mock_private_message):
    """НОВЫЙ ТЕСТ: Проверяет, что сопоставление возвращает None, если сообщение не найдено."""
    db_instance = Database(in_memory_db, mock_bot, mock_private_message, GROUP_ID)
    found_id = await db_instance.get_group_message_id_by_private_message(999)
    assert found_id is None

# --- ТЕСТЫ УПРАВЛЕНИЯ ДАННЫМИ ---

async def test_get_all_users(in_memory_db, mock_bot, mock_private_message):
    """НОВЫЙ ТЕСТ: Проверяет получение списка всех пользователей."""
    db_instance = Database(in_memory_db, mock_bot, mock_private_message, GROUP_ID)
    # Сначала проверяем пустую базу
    users = await db_instance.get_all_users()
    assert users == []
    # Добавляем пользователей
    await in_memory_db.execute('INSERT INTO users (chat_id, topic_id, user_name) VALUES (?, ?, ?)', (1, 10, 'user1'))
    await in_memory_db.execute('INSERT INTO users (chat_id, topic_id, user_name) VALUES (?, ?, ?)', (2, 20, 'user2'))
    await in_memory_db.commit()
    users = await db_instance.get_all_users()
    assert len(users) == 2
    assert users[0].chat_id == 1
    assert users[1].user_name == 'user2'

async def test_delete_topic_messages_removes_all_related_data(in_memory_db, mock_bot, mock_private_message):
    """НОВЫЙ ТЕСТ: Проверяет, что удаление темы очищает все связанные сообщения."""
    await in_memory_db.execute('INSERT INTO users (chat_id, topic_id) VALUES (?, ?)', (USER_ID, TOPIC_ID))
    await in_memory_db.execute('INSERT INTO private_messages (chat_id, message_id, local_id) VALUES (?, ?, ?)', (USER_ID, 100, 1))
    await in_memory_db.execute('INSERT INTO private_messages (chat_id, message_id, local_id) VALUES (?, ?, ?)', (USER_ID, 101, 2))
    await in_memory_db.execute('INSERT INTO group_messages (topic_id, message_id, local_id) VALUES (?, ?, ?)', (TOPIC_ID, 200, 1))
    await in_memory_db.execute('INSERT INTO group_messages (topic_id, message_id, local_id) VALUES (?, ?, ?)', (TOPIC_ID, 201, 2))
    # Также добавляем сообщения для другой темы, которые не должны быть удалены
    await in_memory_db.execute('INSERT INTO group_messages (topic_id, message_id, local_id) VALUES (?, ?, ?)', (999, 300, 1))
    await in_memory_db.commit()

    db_instance = Database(in_memory_db, mock_bot, mock_private_message, GROUP_ID)
    await db_instance.delete_topic_messages(TOPIC_ID)

    # Проверяем, что сообщения для TOPIC_ID удалены
    async with in_memory_db.execute('SELECT COUNT(*) FROM private_messages WHERE chat_id = ?', (USER_ID,)) as c:
        assert (await c.fetchone())[0] == 0
    async with in_memory_db.execute('SELECT COUNT(*) FROM group_messages WHERE topic_id = ?', (TOPIC_ID,)) as c:
        assert (await c.fetchone())[0] == 0
    # Проверяем, что сообщения для другой темы остались
    async with in_memory_db.execute('SELECT COUNT(*) FROM group_messages WHERE topic_id = ?', (999,)) as c:
        assert (await c.fetchone())[0] == 1