from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from test_bot.loader import bot
from test_bot.utils.markup_sources import callback_datas_dashboard, callback_datas_monetization, callback_datas_link_site, \
    callback_datas_proceeds, callback_datas_ui_faq
from test_bot.utils.translator import _

@bot.callback_query_handler(func=lambda call: call.data.startswith(callback_datas_ui_faq))
async def callback_ui_faq(call):
    parent = call.data.split(":")[0]
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(_('btn_back'), callback_data=f"back:{ui_faq.__name__}"))

    await bot.edit_message_media(
        InputMediaPhoto(_(f'{parent.split("-")[0]}-img_{parent.split("-")[1]}'), _(f'{parent.split("-")[0]}-txt_{parent.split("-")[1]}'), parse_mode="HTML"), call.message.chat.id,
        call.message.message_id, reply_markup=markup)



@bot.callback_query_handler(func=lambda call: call.data.startswith(tuple(i['id_inside_button'] for i in callback_datas_monetization)))
async def callback_monetization_type(call):
    parent = call.data.split(":")[0]
    parent_id = f'{"-".join(call.data.split(":")[0].split("-")[:-1])}'
    id = [i["id"] for i in callback_datas_monetization].index(parent_id)
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(_('btn_back'), callback_data=f"back:{id}:{ui_callback_ui_monetization.__name__}"))
    await bot.edit_message_media(
        InputMediaPhoto(_(f'{parent_id}-img_{parent.split("-")[-1]}'),
                        _(f'{parent_id}-txt_{parent.split("-")[-1]}'),
                        parse_mode="HTML"), call.message.chat.id,
        call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(tuple(i['id'] for i in callback_datas_monetization)))
async def callback_ui_monetization(call):
    await ui_callback_ui_monetization(call.message,call.message.message_id, call.data)


@bot.callback_query_handler(func=lambda call: call.data.startswith(tuple(i['id_inside_button'] for i in callback_datas_link_site)))
async def callback_link_type(call):
    parent = call.data.split(":")[0]
    parent_id = f'{"-".join(call.data.split(":")[0].split("-")[:-1])}'
    id = [i["id"] for i in callback_datas_link_site].index(parent_id)
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(_('btn_back'), callback_data=f"back:{id}:{ui_callback_ui_link_site.__name__}"))
    await bot.edit_message_media(
        InputMediaPhoto(_(f'{parent_id}-img_{parent.split("-")[-1]}'),
                        _(f'{parent_id}-txt_{parent.split("-")[-1]}'),
                        parse_mode="HTML"), call.message.chat.id,
        call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(tuple(i['id'] for i in callback_datas_link_site)))
async def callback_ui_link_site(call):
    await ui_callback_ui_link_site(call.message,call.message.message_id, call.data)




@bot.callback_query_handler(func=lambda call: call.data.startswith(tuple(f'{i["id"]}-payment_{i["btn_type"]}' for i in callback_datas_proceeds)))
async def callback_payment_type(call):
    parent = call.data.split(":")[0]
    parent_id = f'{call.data.split(":")[0].split("-")[0]}-{call.data.split(":")[0].split("-")[1]}'

    name = next((i['name'] for i in callback_datas_proceeds if i['id']==parent_id), None)
    btn_type = next((i['btn_type'] for i in callback_datas_proceeds if i['id'] == parent_id), None)
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(_('btn_back'), callback_data=f"back:{parent}:{ui_callback_ui_proceeds.__name__}"))
    if(btn_type=="details"):
        await bot.edit_message_media(
            InputMediaPhoto(_(f'{parent.split("-")[0]}-{parent.split("-")[1]}-img_{parent.split("-")[2]}'), _(f'{parent.split("-")[0]}-{parent.split("-")[1]}-txt_{parent.split("-")[2]}'), parse_mode="HTML"), call.message.chat.id,
            call.message.message_id, reply_markup=markup)
    else:
        await bot.edit_message_media(
            InputMediaPhoto(_(f'{parent.split("-")[0]}-{parent.split("-")[1]}-img_{parent.split("-")[2]}'), _(f'{parent.split("-")[0]}-{parent.split("-")[1]}-txt_{parent.split("-")[2]}',payment_method=name), parse_mode="HTML"), call.message.chat.id,
            call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(tuple(i['id'] for i in callback_datas_proceeds)))
async def callback_ui_proceeds(call):
    await ui_callback_ui_proceeds(call.message,call.message.message_id, call.data)

@bot.callback_query_handler(func=lambda call: call.data.startswith(callback_datas_dashboard))
async def callback_dashboard(call):
    if call.data.startswith(callback_datas_dashboard[0]):
        await ui_faq(call.message, call.message.message_id)
    elif call.data.startswith(callback_datas_dashboard[1]):
        await ui_proceeds(call.message, call.message.message_id)
    elif call.data.startswith(callback_datas_dashboard[2]):
        await ui_last(call.message, call.message.message_id)
    elif call.data.startswith(callback_datas_dashboard[3]):
        await ui_link_site(call.message, call.message.message_id)
    elif call.data.startswith(callback_datas_dashboard[4]):
        await ui_monetization(call.message, call.message.message_id)
    elif call.data.startswith(callback_datas_dashboard[6]):
        await ui_support(call.message, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("back"))
async def back(call):
    back_func = call.data.split(":")[-1]
    if(len(call.data.split(":"))>2):

        await globals()[back_func](call.message, call.message.message_id, ":".join(call.data.split(":")[1:]))
    else:
        await globals()[back_func](call.message, call.message.message_id, call.data)

