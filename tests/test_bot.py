import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from dataclasses import dataclass

# Импортируем сам модуль бота
import main_telebot2
from main_telebot2 import (
    calculate_payment,
    handle_start,
    private_messages,
    group_messages,
    ban_user,
    silent,
    information_group,
    callback_dashboard,
    edited_message
)


# --- MOCK OBJECTS ---

@dataclass
class User:
    """Локальная копия класса User для тестов."""
    chat_id: int
    topic_id: int
    nickname: str
    username: str
    is_ban: bool
    reg_date: str


# --- FIXTURES ---

@pytest.fixture
def mock_bot(mocker):
    """Мок для объекта бота"""
    bot = mocker.patch('main_telebot2.bot', new_callable=AsyncMock)

    bot.reply_to = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.send_video = AsyncMock()
    bot.send_document = AsyncMock()
    bot.edit_message_media = AsyncMock()
    bot.copy_message = AsyncMock()
    bot.send_media_group = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.edit_message_caption = AsyncMock()
    bot.get_chat = AsyncMock()
    return bot


@pytest.fixture
def mock_db():
    """Мок для базы данных"""
    db = AsyncMock()

    test_user = User(
        chat_id=12345,
        topic_id=555,
        nickname="TestUser",
        username="test_login",
        is_ban=False,
        reg_date="2023-01-01 12:00:00.000000"
    )

    db.get_user_by_chat_id.return_value = test_user
    db.get_user_by_topic_id.return_value = test_user
    db.get_or_create_topic.return_value = 555
    db.get_chat_id_by_topic_id.return_value = 12345
    db.get_group_message_id_by_private_message.return_value = 999
    db.get_private_message_id_by_group_message.return_value = 111
    db.update_ban_status_by_topic_id.return_value = "Пользователь заблокирован"

    return db


@pytest.fixture
def message_private():
    """Создает фиктивное сообщение из лички"""
    msg = MagicMock()
    msg.chat.id = 12345
    msg.chat.type = "private"
    msg.text = "Hello"
    msg.from_user.id = 12345
    msg.from_user.username = "test_login"
    msg.from_user.first_name = "Test"
    msg.message_id = 100
    msg.content_type = "text"
    msg.reply_to_message = None
    msg.json = {}

    # !!! ВАЖНО: Явно указываем, что это НЕ пересылка,
    # иначе MagicMock создаст фейковые объекты и бот подумает, что это форвард.
    msg.forward_from = None
    msg.forward_from_chat = None

    return msg


@pytest.fixture
def message_group():
    """Создает фиктивное сообщение из группы"""
    msg = MagicMock()
    msg.chat.id = main_telebot2.GROUP_ID
    msg.chat.type = "supergroup"
    msg.message_thread_id = 555
    msg.text = "Reply from admin"
    msg.from_user.id = 777
    msg.message_id = 200
    msg.content_type = "text"
    msg.json = {'reply_to_message': {'message_id': 150}}

    msg.forward_from = None
    msg.forward_from_chat = None

    return msg


# ==========================================
# ОСНОВНЫЕ ТЕСТЫ
# ==========================================

@pytest.mark.asyncio
async def test_calculate_payment_card(mock_bot, message_private):
    with patch('main_telebot2.load_currency', return_value=(Decimal("90.0"), Decimal("38.0"), Decimal("3.2"))):
        message_private.text = "/card 100 10"
        await calculate_payment(message_private)
        assert mock_bot.reply_to.called
        assert mock_bot.reply_to.call_args[1]['parse_mode'] == 'HTML'


@pytest.mark.asyncio
async def test_private_message_to_group(mock_bot, mock_db, message_private):
    message_private.text = "User message"
    await private_messages(message_private, db=mock_db)

    mock_bot.send_message.assert_called()
    kwargs = mock_bot.send_message.call_args[1]

    # Проверяем вхождение текста, так как бот добавляет заголовок "Отправлено от..."
    assert "User message" in kwargs['text']

    mock_db.add_message_to_db.assert_called_once()


@pytest.mark.asyncio
async def test_group_message_to_private(mock_bot, mock_db, message_group):
    with patch('main_telebot2.check_conflicted_commands', return_value=False):
        await group_messages(message_group, db=mock_db)

        mock_bot.copy_message.assert_called()
        kwargs = mock_bot.copy_message.call_args[1]
        assert kwargs['chat_id'] == 12345


@pytest.mark.asyncio
async def test_ban_user(mock_bot, mock_db, message_group):
    await ban_user(message_group, db=mock_db)
    mock_db.update_ban_status_by_topic_id.assert_called_once()
    mock_bot.reply_to.assert_called_with(message_group, "Пользователь заблокирован")


@pytest.mark.asyncio
async def test_silent_mode(mock_bot, mock_db, message_group):
    main_telebot2.silent_users = []

    await silent(message_group, db=mock_db)
    assert len(main_telebot2.silent_users) == 1
    assert "активирован" in mock_bot.reply_to.call_args[0][1]

    await silent(message_group, db=mock_db)
    assert len(main_telebot2.silent_users) == 0
    assert "деактивирован" in mock_bot.reply_to.call_args[0][1]


@pytest.mark.asyncio
async def test_info_command(mock_bot, mock_db, message_group):
    mock_chat = MagicMock()
    mock_chat.username = "real_username"
    mock_bot.get_chat.return_value = mock_chat

    await information_group(message_group, db=mock_db)
    text = mock_bot.reply_to.call_args[0][1]
    assert "ID: 12345" in text


@pytest.mark.asyncio
async def test_start_command_ui(mock_bot, mock_db, message_private):
    with patch('main_telebot2._', side_effect=lambda key, **kwargs: key):
        await handle_start(message_private, db=mock_db)
        assert mock_bot.send_photo.called


# ==========================================
# ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ (Исправленные)
# ==========================================

@pytest.mark.asyncio
async def test_unban_user(mock_bot, mock_db, message_group):
    banned_user = User(
        chat_id=12345, topic_id=555, nickname="Banned", username="u",
        is_ban=True, reg_date="2023-01-01"
    )
    mock_db.get_user_by_topic_id.return_value = banned_user
    mock_db.update_ban_status_by_topic_id.return_value = "Пользователь разблокирован"

    await ban_user(message_group, db=mock_db)
    mock_bot.reply_to.assert_called_with(message_group, "Пользователь разблокирован")


@pytest.mark.asyncio
async def test_video_message_private(mock_bot, mock_db, message_private):
    """Тест отправки ВИДЕО из лички"""
    message_private.content_type = "video"
    message_private.text = None
    message_private.caption = "Look at video"

    video_mock = MagicMock()
    video_mock.file_id = "VID_123"
    message_private.video = video_mock

    await private_messages(message_private, db=mock_db)

    mock_bot.send_video.assert_called()
    kwargs = mock_bot.send_video.call_args[1]

    assert kwargs['video'] == "VID_123"
    # ИСПРАВЛЕНИЕ: Используем 'in', так как бот добавляет "Отправлено от..."
    assert "Look at video" in kwargs['caption']


@pytest.mark.asyncio
async def test_weekend_notification(mock_bot, mock_db, message_private):
    main_telebot2.weekend = True
    main_telebot2.send_weekend_users = []

    await private_messages(message_private, db=mock_db)

    assert mock_bot.reply_to.called
    assert "у сервиса выходной" in mock_bot.reply_to.call_args[0][1]

    mock_bot.reply_to.reset_mock()
    await private_messages(message_private, db=mock_db)
    mock_bot.reply_to.assert_not_called()

    main_telebot2.weekend = False


@pytest.mark.asyncio
async def test_latehour_notification(mock_bot, mock_db, message_private):
    main_telebot2.latehour = True
    main_telebot2.send_latehour_users = []

    await private_messages(message_private, db=mock_db)

    assert mock_bot.reply_to.called
    assert "после 19:00" in mock_bot.reply_to.call_args[0][1]

    main_telebot2.latehour = False


@pytest.mark.asyncio
async def test_document_edit_caption(mock_bot, mock_db, message_private):
    """Тест РЕДАКТИРОВАНИЯ подписи документа"""
    message_private.content_type = "document"
    message_private.caption = "New Caption"

    doc_mock = MagicMock()
    doc_mock.file_id = "DOC_123"
    message_private.document = doc_mock

    await edited_message(message_private, db=mock_db)

    mock_bot.edit_message_caption.assert_called()
    kwargs = mock_bot.edit_message_caption.call_args[1]

    # ИСПРАВЛЕНИЕ: Используем 'in'
    assert "New Caption" in kwargs['caption']
    assert kwargs['chat_id'] == main_telebot2.GROUP_ID


@pytest.mark.asyncio
async def test_unknown_command_in_group(mock_bot, mock_db, message_group):
    message_group.text = "/random_cmd 123"

    with patch('main_telebot2.check_conflicted_commands', return_value=False):
        await group_messages(message_group, db=mock_db)
        mock_bot.copy_message.assert_called()