import asyncio
import time

from pyrogram import Client, filters, idle
import uvloop

api_id = 22589564
api_hash = "53bedf3feef46f4b2a87492a3e2985c4"
TARGET_CHAT_ID = -1002400778400
TARGET_TOPIC_ID = 7
TARGET_BOT = "@maraphon4ik_bot"
app = Client("my_account",api_id=api_id, api_hash=api_hash)

tests = [
]
count_test = 1

@app.on_message(filters.chat(TARGET_CHAT_ID))
def private_messages(client,message):
    global count_test
    if message.reply_to_message.id == TARGET_TOPIC_ID:

        if(tests[0]['side']=='private'):

                if(tests[0]['type']=='text'):

                        me = app.get_me()
                        if(message.text==f"Отправлено от {me.username or me.first_name}\n{tests[0]['except_text']}"):
                            print(f"Test {count_test}: SUCCESS")
                        else:
                            got_text = message.text.split(f'Отправлено от {me.username or me.first_name}\n')[-1]
                            print(f"Test {count_test}: FAIL, excepted: {tests[0]['except_text']}, got: {got_text}")
                        tests.pop(0)
                        count_test+=1
@app.on_message(filters.chat(TARGET_BOT))
def group_messages(client,message):
    global count_test
    if (tests[0]['side'] == 'group'):

        if (tests[0]['type'] == 'text'):

            me = app.get_me()
            if (message.text == tests[0]['except_text']):
                print(f"Test {count_test}: SUCCESS")
            else:
                print(f"Test {count_test}: FAIL, excepted: {tests[0]['except_text']}, got: {message.text}")
            tests.pop(0)
            count_test += 1

@app.on_edited_message(filters.chat(TARGET_BOT))
async def handle_edit(client, message):
    print(f"Сообщение изменено! Новый текст: {message.text}")


def test_default_private_text(send_message, is_test = True):
    if(is_test):
        tests.append({"type": "text", "except_text": send_message, "side": "private"})

    mess = app.send_message(TARGET_BOT, send_message)
    time.sleep(5)
    return mess

def test_default_group_text(send_message, is_test = True):
    if (is_test):
        tests.append({"type": "text", "except_text": send_message, "side": "group"})
    mess = app.send_message(TARGET_CHAT_ID, send_message, message_thread_id=TARGET_TOPIC_ID)
    time.sleep(5)
    return mess

def test_default_text(send_message):
    test_default_group_text(send_message)
    test_default_private_text(send_message)

def test_edit_text_private(text):
    mess = test_default_private_text("будет отредактировано", False)
    app.edit_message_text(TARGET_BOT,mess.id,text)

@app.on_message(filters.command("test", prefixes="/"))
def start_command(client, message):
    message.reply("Команда получена!")
    # test_default_text("test")
    # test_default_text("*Не закрытая жирность")
    # test_default_text("[Текст без ссылки](")
    test_edit_text_private("отредактировано")

# uvloop.install()
app.run()
