from decimal import Decimal

from telebot.types import InputFile

from ...handlers.private.markups import start_markup
from ...loader import bot, is_parasite, prefix_folder, ADMINS
from ...utils.calc import MAX_AMOUNT_NUM, load_currency, PAYPAL_PERCENT, PAYPAL_FIX, _SERVICES, CRYPTO_RATE, YOUTUBE_FIX
from ...utils.io import load_work_chats, save_work_chats
from ...utils.translator import _
from ...utils.math_and_types import is_number, quantize

private_func = lambda message: message.chat.type == "private"

@bot.message_handler(commands=['start'], func=private_func)
async def handle_start(message, album: list = None, db=None, checker=None):
    if db is None:
        await bot.reply_to(message, "Ошибка подключения к базе данных ")
        return
    all_users = await db.get_all_users()
    user_name = message.from_user.username or message.from_user.first_name
    if(is_parasite):
        msg = await bot.send_photo(message.chat.id, _('start_message-file_id'), caption=_('start_message'), parse_mode='HTML')
        await start_markup(message,msg.message_id)
        await bot.reply_to(message,_("start_reply"), parse_mode="HTML")
    else:
        await bot.send_photo(message.chat.id, InputFile(f"{prefix_folder}main.png"), caption=_('start-message', name=user_name), parse_mode='HTML')
@bot.message_handler(commands=['card', 'crypto'], func=private_func)
async def calculate_payment(message):
    splitted_text = message.text.split()

    cmd = splitted_text[0].replace("/", "").lower()

    s_args = splitted_text[1:]

    if (
            not s_args
            or len(s_args) < 2
            or any(not is_number(arg) for arg in s_args[:2])
    ):
        # Ключ заменен на подчеркивание: errors.none... -> errors_none...
        await bot.reply_to(message, _("errors_none_or_less_two"), parse_mode='HTML')
        return

    amount = Decimal(s_args[0])

    if not (0 <= amount <= MAX_AMOUNT_NUM):
        await bot.reply_to(message, _("errors_large_num"), parse_mode='HTML')
        return

    commission = Decimal(s_args[1])

    rub, uah, byn = load_currency()

    total = Decimal(0)
    outcast_commission = Decimal(0)
    _service = None

    if len(s_args) == 2:
        amount -= amount * (PAYPAL_PERCENT / 100)
        outcast_commission = (amount - PAYPAL_FIX) * (commission / 100)
        total = quantize(amount - PAYPAL_FIX - outcast_commission)
    else:
        _service = s_args[2].lower()

        if _service not in _SERVICES:
            await bot.reply_to(message, _("errors_unknown_service"), parse_mode='HTML')
            return

        service = _SERVICES[_service]

        if _service == "ff":
            outcast_commission = (amount - PAYPAL_FIX) * (commission / 100)
            total = quantize(amount - PAYPAL_FIX - outcast_commission)

        elif _service == "bs":
            amount *= service
            outcast_commission = (amount - PAYPAL_FIX) * (commission / 100)
            total = quantize(amount - PAYPAL_FIX - outcast_commission)

        elif _service == "y":
            youtube_commission = amount * service / 100
            outcast_commission = amount * (commission / 100)
            total = quantize(amount - youtube_commission - outcast_commission)

    # Собираем данные
    _kwargs = {
        "amount": amount,
        "commission": commission,
        "total": total,
    }

    if cmd == "crypto":  # PaymentType.CRYPTO
        key = "crypto"
        _kwargs["usdt"] = quantize(total * CRYPTO_RATE)  # Заменил CRYPTO на CRYPTO_RATE (константа)
    else:
        key = "card"
        _kwargs.update({
            "to_rub": quantize(total * rub),
            "to_uah": quantize(total * (rub * (Decimal("10") / uah))),
            "to_byn": quantize(total * (rub * (Decimal("1") / byn))),
        })

    # Формирование суффикса (заменил точки на _)
    if _service is None:
        _kwargs["paypal_fix"] = PAYPAL_FIX
        key += "_default"
    elif _service == "ff":
        _kwargs["paypal_fix"] = PAYPAL_FIX
        key += "_friends_and_family"
    elif _service == "bs":
        _kwargs["paypal_fix"] = PAYPAL_FIX
        key += "_beatstars"
    elif _service == "y":
        _kwargs.update({
            "youtube_fix": YOUTUBE_FIX,
            "youtube_commission": quantize(amount * Decimal("0.10")),
        })
        key += "_youtube"

    final_kwargs = {}
    for k, v in _kwargs.items():
        if isinstance(v, Decimal):
            if k in ["to_rub", "to_uah"]:  # Рубли и гривны обычно без копеек
                final_kwargs[k] = f"{v:.2f}"
            else:
                final_kwargs[k] = f"{v:.2f}"
        else:
            final_kwargs[k] = v

    await bot.reply_to(message, _(key, **final_kwargs), parse_mode='HTML',disable_web_page_preview=True)

work_chats = load_work_chats()
@bot.message_handler(commands=['remove_work_chat'], func=private_func)
async def handle_remove_work_chat(message):
    if message.chat.id in ADMINS:
        args = message.text.split()
        if len(args) != 2:
            await bot.reply_to(message, "Usage: /remove_work_chat <topic_id>")
            return
        try:
            topic_id = int(args[1])
            if topic_id in work_chats:
                work_chats.remove(topic_id)
                await save_work_chats(work_chats)
                await bot.reply_to(message, f"Topic ID {topic_id} removed from work chats.")
            else:
                await bot.reply_to(message, f"Topic ID {topic_id} is not in the work chats list.")
        except ValueError:
            await bot.reply_to(message, "Invalid topic ID. Please provide a valid integer.")
    else:
        await bot.reply_to(message, "You don't have permission to use this command.")
@bot.message_handler(commands=['add_work_chat'], func=private_func)
async def handle_add_work_chat(message):
    if message.chat.id in ADMINS:
        args = message.text.split()
        if len(args) != 2:
            await bot.reply_to(message, "Usage: /add_work_chat <topic_id>")
            return
        try:
            topic_id = int(args[1])
            work_chats.add(topic_id)
            await save_work_chats(work_chats)
            await bot.reply_to(message, f"Topic ID {topic_id} added to work chats.")
        except ValueError:
            await bot.reply_to(message, "Invalid topic ID. Please provide a valid integer.")
    else:
        await bot.reply_to(message, "You don't have permission to use this command.")