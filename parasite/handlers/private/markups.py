from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from test_bot.loader import bot
from test_bot.utils.markup_sources import callback_datas_dashboard, callback_datas_ui_faq, callback_datas_proceeds, \
    callback_datas_link_site, callback_datas_monetization
from test_bot.utils.translator import _


async def start_markup(message,message_id,calldata=None):
    markup = InlineKeyboardMarkup()
    for i in callback_datas_dashboard:
        markup.add(InlineKeyboardButton(_(f'btn_{i}'), callback_data=f"{i}:", url= "https://t.me/GetAccessCreator_bot" if i=='subscription' else None))

    await bot.edit_message_media(InputMediaPhoto(_('start_message-file_id'),_('start_message'),parse_mode="HTML"), message.chat.id,message_id, reply_markup=markup)


async def ui_faq(message,message_id,calldata=None):
    markup = InlineKeyboardMarkup()
    print("уже работает")
    for i in callback_datas_ui_faq:
        markup.add(InlineKeyboardButton(_(f'{i.split("-")[0]}-btn_{i.split("-")[1]}'), callback_data=f"{i}:"))
    markup.add(InlineKeyboardButton(_("btn_back"),callback_data=f"back:{start_markup.__name__}"))
    await bot.edit_message_media(InputMediaPhoto(_('faq-file_id'), _('txt_faq'), parse_mode="HTML"), message.chat.id,message_id, reply_markup=markup)





async def ui_proceeds(message,message_id,calldata=None):
    markup = InlineKeyboardMarkup()
    for i in callback_datas_proceeds:
        markup.add(InlineKeyboardButton(_(f'{i["id"].split("-")[0]}-btn_{i["id"].split("-")[1]}'),callback_data=f'{i["id"]}:'))
    markup.add(InlineKeyboardButton(_("btn_back"), callback_data=f"back:{start_markup.__name__}"))
    await bot.edit_message_media(InputMediaPhoto(_('img_proceeds'), _('txt_proceeds'), parse_mode="HTML"), message.chat.id,
                                 message_id, reply_markup=markup)

async def ui_callback_ui_proceeds(message,message_id,calldata=None):
    parent = f'{calldata.split(":")[0].split("-")[0]}-{calldata.split(":")[0].split("-")[1]}'
    btn_type = next((i['btn_type'] for i in callback_datas_proceeds if i['id'] == parent), None)
    name = next((i['name'] for i in callback_datas_proceeds if i['id'] == parent), None)
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(_(f'{parent}-btn_payment_{btn_type}'), callback_data=f"{parent}-payment_{btn_type}"))
    markup.add(
        InlineKeyboardButton(_('btn_back'), callback_data=f"back:{ui_proceeds.__name__}"))

    await bot.edit_message_media(
        InputMediaPhoto(_(f'{parent.split("-")[0]}-img_{parent.split("-")[1]}'),
                        _(f'{parent.split("-")[0]}-txt_{parent.split("-")[1]}',payment_method=name),
                        parse_mode="HTML"), message.chat.id,
        message.message_id, reply_markup=markup)





async def ui_link_site(message,message_id,callback=None):
    markup = InlineKeyboardMarkup()
    for i in callback_datas_link_site:
        markup.add(InlineKeyboardButton(_(f'{i["id"].split("-")[0]}-btn_{i["id"].split("-")[1]}'), callback_data=f'{i["id"]}:'))
    markup.add(InlineKeyboardButton(_("btn_back"),callback_data=f"back:{start_markup.__name__}"))
    await bot.edit_message_media(InputMediaPhoto(_('img_link_site'), _('txt_link_site'), parse_mode="HTML"), message.chat.id,message_id, reply_markup=markup)

async def ui_callback_ui_link_site(message,message_id,calldata=None):
    parent = None
    if(calldata.split(":")[0].isdigit()):
        parent = callback_datas_link_site[int(calldata.split(":")[0])]['id']
    else:
        parent = f'{calldata.split(":")[0].split("-")[0]}-{calldata.split(":")[0].split("-")[1]}'
    id_inside_button = next((i['id_inside_button'] for i in callback_datas_link_site if i['id'] == parent), None)
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(_(f'{"-".join(id_inside_button.split("-")[:-1])}-btn_{id_inside_button.split("-")[-1]}'), callback_data=f"{id_inside_button}:"))
    markup.add(
        InlineKeyboardButton(_('btn_back'), callback_data=f"back:{ui_link_site.__name__}"))

    await bot.edit_message_media(
        InputMediaPhoto(_(f'{parent.split("-")[0]}-img_{parent.split("-")[1]}'),
                        _(f'{parent.split("-")[0]}-txt_{parent.split("-")[1]}'),
                        parse_mode="HTML"), message.chat.id,
        message.message_id, reply_markup=markup)



async def ui_monetization(message,message_id, calldata=None):
    markup = InlineKeyboardMarkup()
    for i in callback_datas_monetization:
        markup.add(InlineKeyboardButton(_(f'{i["id"].split("-")[0]}-btn_{i["id"].split("-")[1]}'), callback_data=f'{i["id"]}:'))
    markup.add(InlineKeyboardButton(_("btn_back"),callback_data=f"back:{start_markup.__name__}"))
    await bot.edit_message_media(InputMediaPhoto(_('img_monetization'), _('txt_monetization'), parse_mode="HTML"), message.chat.id,message_id, reply_markup=markup)


async def ui_callback_ui_monetization(message,message_id,calldata=None):
    parent = None

    if(calldata.split(":")[0].isdigit()):
        parent = callback_datas_monetization[int(calldata.split(":")[0])]['id']
    else:
        parent = f'{calldata.split(":")[0].split("-")[0]}-{calldata.split(":")[0].split("-")[1]}'
    id_inside_button = next((i['id_inside_button'] for i in callback_datas_monetization if i['id'] == parent), None)
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(_(f'{"-".join(id_inside_button.split("-")[:-1])}-btn_{id_inside_button.split("-")[-1]}'), callback_data=f"{id_inside_button}:"))
    markup.add(
        InlineKeyboardButton(_('btn_back'), callback_data=f"back:{ui_monetization.__name__}"))

    await bot.edit_message_media(
        InputMediaPhoto(_(f'{parent.split("-")[0]}-img_{parent.split("-")[1]}'),
                        _(f'{parent.split("-")[0]}-txt_{parent.split("-")[1]}'),
                        parse_mode="HTML"), message.chat.id,
        message.message_id, reply_markup=markup)




async def ui_support(message,message_id, calldata=None):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(_("btn_back"),callback_data=f"back:{start_markup.__name__}"))
    await bot.edit_message_media(InputMediaPhoto(_('img_support'), _('txt_support'), parse_mode="HTML"), message.chat.id,message_id, reply_markup=markup)

async def ui_last(message,message_id, calldata=None):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(_("btn_back"),callback_data=f"back:{start_markup.__name__}"))
    await bot.edit_message_media(InputMediaPhoto(_('img_last_button'), _('txt_last_button'), parse_mode="HTML"), message.chat.id,message_id, reply_markup=markup)
