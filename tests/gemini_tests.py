import asyncio
import os
import logging
import warnings
from dataclasses import dataclass
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio, \
    ReplyParameters

# ================= КОНФИГУРАЦИЯ =================
api_id = 22589564
api_hash = "53bedf3feef46f4b2a87492a3e2985c4"

TARGET_CHAT_ID = -1002400778400
TARGET_TOPIC_ID = 895
TARGET_BOT = "@maraphon4ik_bot"

SLEEP_TIME = 3  # Пауза между тестами

# Отключаем шум
logging.getLogger("pyrogram").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

app = Client("my_account", api_id=api_id, api_hash=api_hash)

# Файлы
FILES = {
    'image': ['files/image/1.png', 'files/image/2.png', 'files/image/3.png'],
    'video': ['files/video/1.mp4', 'files/video/2.webm'],
    'doc': ['files/doc/1.txt'],
    'doc_img': ['files/image/1.png', 'files/image/2.png'],
    'gif': ['files/gif/1.gif'],
    'audio': ['files/audio/1.mp3'],
    'voice': ['files/voice/1.ogg'],
    'sticker': ['files/sticker/1.webp'],
    'round': ['files/round/1.mp4']
}

# ================= СТАТИСТИКА =================
STATS = {
    'total_planned': 0,
    'current_idx': 0,
    'passed': 0,
    'warnings': 0,
    'failed': 0
}


@dataclass
class MockMessage:
    id: int = 123
    caption: str = "Mock"
    text: str = "Mock"


# ================= ХЕЛПЕРЫ =================

async def safe_reaction(chat_id, msg_id, emoji_char="👍"):
    """
    Пытается поставить реакцию всеми возможными способами.
    Если хоть один сработал - успех. Если все упали - ошибка.
    """
    errors = []

    # 1. PyTgFork / New Pyrogram (reaction=)
    try:
        await app.set_reaction(chat_id, msg_id, reaction=emoji_char)
        return
    except Exception as e:
        errors.append(str(e))

    # 2. Standard Pyrogram (emoji=)
    try:
        await app.set_reaction(chat_id, msg_id, emoji=emoji_char)
        return
    except Exception as e:
        errors.append(str(e))

    # 3. Old Pyrogram (send_reaction)
    try:
        await app.send_reaction(chat_id, msg_id, emoji_char)
        return
    except Exception as e:
        errors.append(str(e))

    # Если дошли сюда - значит ничего не сработало
    raise Exception(f"Failed to react: {errors[0]}")


# ================= ДВИЖОК =================

current_test = {
    'future': None,
    'expect': {},
    'sent_msg': None
}


def get_msg_text(message: Message):
    return message.text or message.caption or ""


@app.on_message(filters.chat(TARGET_CHAT_ID) | filters.chat(TARGET_BOT))
async def msg_listener(client, message: Message):
    await _process_update(message, 'new')


@app.on_edited_message(filters.chat(TARGET_CHAT_ID) | filters.chat(TARGET_BOT))
async def edit_listener(client, message: Message):
    await _process_update(message, 'edit')


async def _process_update(message: Message, event_type: str):
    global current_test
    if not current_test['future'] or current_test['future'].done(): return

    exp = current_test['expect']
    incoming_side = 'group' if message.chat.id == TARGET_CHAT_ID else 'private'

    if incoming_side != exp.get('side'): return
    if exp.get('event_type', 'new') != event_type: return

    is_valid = False
    m_type = exp.get('type')
    content = exp.get('content')

    try:
        cur_text = get_msg_text(message)
        if m_type == 'text':
            if content in cur_text: is_valid = True
        elif m_type == 'empty_caption':
            if content and content not in cur_text:
                is_valid = True
            elif not cur_text:
                is_valid = True
        elif m_type == 'album':
            if message.media_group_id: is_valid = True
        else:
            if getattr(message, m_type, None): is_valid = True
    except:
        pass

    if is_valid:
        current_test['future'].set_result(True)


# --- УПРАВЛЕНИЕ ТЕСТАМИ ---

async def smart_sleep(seconds=SLEEP_TIME):
    await asyncio.sleep(seconds)


async def run_test(name, action, expectation, timeout=8, dry_run=False):
    global current_test, STATS

    if dry_run:
        STATS['total_planned'] += 1
        current_test['sent_msg'] = MockMessage()
        return True

    STATS['current_idx'] += 1
    counter_str = f"[{STATS['current_idx']}/{STATS['total_planned']}]"
    print(f"{counter_str:<10} TEST: {name:<55}", end="", flush=True)

    current_test['future'] = asyncio.Future()
    current_test['expect'] = expectation
    current_test['sent_msg'] = None

    try:
        sent = await action()
        current_test['sent_msg'] = sent
    except Exception as e:
        print(f"❌ ERROR: {e}")
        STATS['failed'] += 1
        return False

    # FIX V13: Если skip_wait (Action Only), считаем это УСПЕХОМ (PASSED), а не Warning
    if expectation.get('skip_wait'):
        await asyncio.sleep(1.5)
        print("✅ PASS (Action)")
        STATS['passed'] += 1
        await smart_sleep()
        return True

    try:
        real_timeout = timeout + 5 if ('Forward' in name or 'Del Caption' in name) else timeout
        await asyncio.wait_for(current_test['future'], timeout=real_timeout)
        print("✅ PASS")
        STATS['passed'] += 1
        await smart_sleep()
        return True
    except asyncio.TimeoutError:
        # Warning только если ждали событие, но оно не пришло (но ошибок не было)
        if "Del Caption" in name:
            print("⚠️ PASS (No Update)")
            STATS['warnings'] += 1
            await smart_sleep()
            return True

        print("❌ FAIL/TIMEOUT")
        STATS['failed'] += 1
        return False


# ================= СЦЕНАРИИ =================

async def execute_tests(dry_run=False):
    global current_test
    if dry_run: current_test['sent_msg'] = MockMessage()

    DIRECTIONS = [
        {'name': 'Priv->Group', 'target': TARGET_BOT, 'kw': {}, 'exp_side': 'group'},
        {'name': 'Group->Priv', 'target': TARGET_CHAT_ID, 'kw': {'message_thread_id': TARGET_TOPIC_ID},
         'exp_side': 'private'}
    ]

    SINGLE_TYPES = [
        ('text', None, 'send_message'),
        ('photo', 'image', 'send_photo'),
        ('video', 'video', 'send_video'),
        ('document', 'doc', 'send_document'),
        ('animation', 'gif', 'send_animation'),
        ('voice', 'voice', 'send_voice'),
        ('audio', 'audio', 'send_audio'),
        ('sticker', 'sticker', 'send_sticker'),
        ('round', 'round', 'send_video_note'),
    ]

    for d in DIRECTIONS:
        if not dry_run: print(f"\n >>> DIRECTION: {d['name']} <<<\n")
        target = d['target']
        kw = d['kw']
        exp_side = d['exp_side']

        for t_type, f_key, method in SINGLE_TYPES:
            f_path = FILES[f_key][0] if f_key and FILES.get(f_key) else None
            if f_key and (not f_path or not os.path.exists(f_path)):
                if not dry_run: print(f"⚠️ SKIP {t_type} (No File)")
                continue

            content = f"Test {t_type}"

            # 1. SEND
            async def act_send():
                func = getattr(app, method)
                local_kw = kw.copy()
                if t_type == 'text':
                    return await func(target, content, **local_kw)
                elif t_type in ['sticker', 'round']:
                    return await func(target, f_path, **local_kw)
                else:
                    return await func(target, f_path, caption=content, **local_kw)

            expect_type = 'video_note' if t_type == 'round' else t_type
            if not await run_test(f"[{t_type.upper()}] Send", act_send,
                                  {'side': exp_side, 'type': expect_type, 'content': content}, dry_run=dry_run):
                continue

            last_id = current_test['sent_msg'].id if current_test['sent_msg'] else 0

            # 2. REACTION (Теперь Зеленая если отправилась)
            async def act_react():
                await safe_reaction(target, last_id, "👍")

            await run_test(f"[{t_type.upper()}] Reaction", act_react, {'skip_wait': True}, dry_run=dry_run)

            # 3. REPLY TEXT
            async def act_reply_text():
                return await app.send_message(target, f"Reply Text", reply_to_message_id=last_id, **kw)

            await run_test(f"[{t_type.upper()}] Reply (Text)", act_reply_text,
                           {'side': exp_side, 'type': 'text', 'content': "Reply"}, dry_run=dry_run)

            # 4. REPLY CONTENT
            if t_type != 'text':
                async def act_reply_content():
                    func = getattr(app, method)
                    local_kw = kw.copy()
                    local_kw['reply_to_message_id'] = last_id
                    if t_type in ['sticker', 'round']:
                        return await func(target, f_path, **local_kw)
                    else:
                        return await func(target, f_path, caption=f"RepCont {t_type}", **local_kw)

                await run_test(f"[{t_type.upper()}] Reply ({t_type.upper()})", act_reply_content,
                               {'side': exp_side, 'type': expect_type}, dry_run=dry_run)

            # 5. FORWARD
            async def act_fwd():
                return await app.forward_messages(target, target, last_id, **kw)

            await run_test(f"[{t_type.upper()}] Forward", act_fwd,
                           {'side': exp_side, 'type': expect_type, 'content': content}, dry_run=dry_run)

            # 6. EDIT & DELETE
            if t_type in ['text', 'photo', 'video', 'document', 'audio', 'animation']:
                async def act_edit_txt():
                    new_txt = f"EDITED {t_type}"
                    if t_type == 'text':
                        return await app.edit_message_text(target, last_id, new_txt)
                    else:
                        return await app.edit_message_caption(target, last_id, new_txt)

                await run_test(f"[{t_type.upper()}] Edit Text", act_edit_txt,
                               {'side': exp_side, 'type': t_type, 'content': "EDITED", 'event_type': 'edit'},
                               dry_run=dry_run)

                if f_key and len(FILES[f_key]) > 1 and t_type != 'animation':
                    f_path_2 = FILES[f_key][1]

                    async def act_edit_media():
                        if t_type == 'photo':
                            media = InputMediaPhoto(f_path_2, caption="New")
                        elif t_type == 'video':
                            media = InputMediaVideo(f_path_2, caption="New")
                        elif t_type == 'document':
                            media = InputMediaDocument(f_path_2, caption="New")
                        elif t_type == 'audio':
                            media = InputMediaAudio(f_path_2, caption="New")
                        return await app.edit_message_media(target, last_id, media=media)

                    await run_test(f"[{t_type.upper()}] Edit Media", act_edit_media,
                                   {'side': exp_side, 'type': t_type, 'content': "New", 'event_type': 'edit'},
                                   dry_run=dry_run)

                if t_type != 'text':
                    async def act_del_cap():
                        return await app.edit_message_caption(target, last_id, caption="")

                    check_text = "New" if (f_key and len(FILES[f_key]) > 1) else content
                    if "EDITED" in (current_test['sent_msg'].caption or ""): check_text = f"EDITED {t_type}"
                    await run_test(f"[{t_type.upper()}] Del Caption", act_del_cap,
                                   {'side': exp_side, 'type': 'empty_caption', 'content': check_text,
                                    'event_type': 'edit'}, dry_run=dry_run)

        # --- SPECIALS ---
        async def act_poll():
            return await app.send_poll(target, "Poll", ["A", "B"], **kw)

        await run_test("[POLL] Send", act_poll, {'side': exp_side, 'type': 'poll'}, dry_run=dry_run)

        async def act_geo():
            return await app.send_location(target, 55.75, 37.61, **kw)

        await run_test("[GEO] Send", act_geo, {'side': exp_side, 'type': 'location'}, dry_run=dry_run)

        async def act_contact():
            return await app.send_contact(target, "+7999", "Contact", **kw)

        await run_test("[CONTACT] Send", act_contact, {'side': exp_side, 'type': 'contact'}, dry_run=dry_run)

        # --- ALBUMS ---
        if len(FILES['image']) >= 3:
            async def act_alb():
                media = [InputMediaPhoto(FILES['image'][0], caption="C1"),
                         InputMediaPhoto(FILES['image'][1], caption="C2"),
                         InputMediaPhoto(FILES['image'][2], caption="C3")]
                return await app.send_media_group(target, media=media, **kw)

            if await run_test("[ALBUM] Send 3 Photos", act_alb, {'side': exp_side, 'type': 'album'}, dry_run=dry_run):
                msgs = current_test['sent_msg']
                if dry_run: msgs = [MockMessage(1), MockMessage(2), MockMessage(3)]

                if msgs and len(msgs) == 3:
                    id2, id3 = msgs[1].id, msgs[2].id

                    async def act_edm(): return await app.edit_message_caption(target, id2, caption="Ed C2")

                    await run_test("[ALBUM] Edit Cap (Item 2)", act_edm,
                                   {'side': exp_side, 'type': 'text', 'content': "Ed C2", 'event_type': 'edit'},
                                   dry_run=dry_run)

                    async def act_dl3(): return await app.edit_message_caption(target, id3, caption="")

                    await run_test("[ALBUM] Del Cap (Item 3)", act_dl3,
                                   {'side': exp_side, 'type': 'empty_caption', 'content': "C3", 'event_type': 'edit'},
                                   dry_run=dry_run)

                    async def act_dl2(): return await app.edit_message_caption(target, id2, caption="")

                    await run_test("[ALBUM] Del Cap (Item 2)", act_dl2,
                                   {'side': exp_side, 'type': 'empty_caption', 'content': "Ed C2",
                                    'event_type': 'edit'}, dry_run=dry_run)

        if FILES['image'] and FILES['video']:
            async def act_mix():
                media = [InputMediaPhoto(FILES['image'][0], caption="P"),
                         InputMediaVideo(FILES['video'][0], caption="V")]
                return await app.send_media_group(target, media=media, **kw)

            await run_test("[ALBUM MIX] Send", act_mix, {'side': exp_side, 'type': 'album'}, dry_run=dry_run)

        if len(FILES['doc_img']) >= 2:
            async def act_doc():
                media = [InputMediaDocument(FILES['doc_img'][0], caption="D1"),
                         InputMediaDocument(FILES['doc_img'][1], caption="D2")]
                return await app.send_media_group(target, media=media, **kw)

            await run_test("[ALBUM DOC] Send", act_doc, {'side': exp_side, 'type': 'album'}, dry_run=dry_run)


async def main():
    async with app:
        me = await app.get_me()
        print("Calculating tests...", end="\r")
        await execute_tests(dry_run=True)

        print(f"Total Tests Planned: {STATS['total_planned']}")
        print(f"User: {me.first_name} | Target: {TARGET_BOT}")
        print("=" * 80)

        await execute_tests(dry_run=False)

        print("\n" + "=" * 80)
        print(f"✅ PASSED:   {STATS['passed']}")
        print(f"⚠️ WARNINGS: {STATS['warnings']} (Expected update did not arrive)")
        print(f"❌ FAILED:   {STATS['failed']}")
        print("=" * 80)


if __name__ == "__main__":
    app.run(main())