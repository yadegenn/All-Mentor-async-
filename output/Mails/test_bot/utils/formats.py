from pydoc import html

from telebot.types import MessageEntity


def formating(text: str | None,last_entities, new_entities, last_text):
    if (last_text == None):
        last_text = ""
    count_text = len(text)
    if last_entities is not None:

        for entity in last_entities:
            new_entity = MessageEntity(
                type=entity.type,
                offset=entity.offset + count_text,
                length=entity.length,
                url=getattr(entity, 'url', None),
                user = entity.user,
                custom_emoji_id=entity.custom_emoji_id,
                language=str(entity.language)
            )
            new_entities.append(new_entity)
    return (text+last_text), new_entities

def text_message_format(message, edit=False):
    user_name = html.escape(message.from_user.username or message.from_user.first_name)
    result_text, result_entities = message.text, message.entities

    if (message.forward_from or message.forward_from_chat):

        forward_user_name = html.escape(
            message.forward_from_chat.title or message.forward_from.username if message.forward_from_chat else message.forward_from.username or message.forward_from.first_name)
        prefix = f"Отправлено от {user_name} «переслали от {forward_user_name}»\n"
        count_text = len(prefix)
        if (message.text):
            count_text = count_text+len(message.text)
        if(count_text>=4096):
            return message.text, message.entities
        result_text, result_entities = formating(
            prefix, message.entities, [
                MessageEntity(type="blockquote", offset=0,
                              length=14 + len(user_name) + 15 + len(forward_user_name) + 2),
                MessageEntity(type="text_link", offset=0, length=14 + len(user_name),
                              url=f'tg://user?id={message.from_user.id}'),
                MessageEntity(type="text_link", offset=15 + len(user_name),
                              length=15 + len(forward_user_name) + 1,
                              url=f'https://t.me/{message.forward_from_chat.username}' if message.forward_from_chat else f'tg://user?id={message.forward_from.id}')
            ], message.text)
    else:
        prefix = f"Отправлено от {user_name}{' (edited)' if edit else ''}\n"
        count_text = len(prefix)
        if (message.text):
            count_text = count_text + len(message.text)
        if (count_text >= 4096):
            return message.text, message.entities
        result_text, result_entities = formating(prefix, message.entities, [
            MessageEntity(type="blockquote", offset=0, length=14 + len(user_name) + 1 + (9 if edit else 0)),
            MessageEntity(type="text_link", offset=0, length=14 + len(user_name) + 1,
                          url=f'tg://user?id={message.from_user.id}')], message.text)
    return result_text, result_entities

def caption_messages(message, edit=False):
    user_name = html.escape(message.from_user.username or message.from_user.first_name)
    result_text, result_entities = message.caption, message.caption_entities
    if (message.forward_from or message.forward_from_chat):
      forward_user_name = html.escape(message.forward_from_chat.title or message.forward_from.username if message.forward_from_chat else message.forward_from.username or message.forward_from.first_name)
      prefix = f"Отправлено от {user_name} «переслали от {forward_user_name}»\n"
      count_text = len(prefix)
      if (message.caption):
          count_text = count_text + len(message.caption)
      if (count_text >= 1024):
          return message.caption, message.caption_entities
      result_text, result_entities = formating(
          prefix, message.caption_entities, [
              MessageEntity(type="blockquote", offset=0,
                            length=14 + len(user_name) + 15 + len(forward_user_name) + 2),
              MessageEntity(type="text_link", offset=0, length=14 + len(user_name),
                            url=f'tg://user?id={message.from_user.id}'),
              MessageEntity(type="text_link", offset=15 + len(user_name),
                            length=15 + len(forward_user_name) + 1,
                            url=f'https://t.me/{message.forward_from_chat.username}' if message.forward_from_chat else f'tg://user?id={message.forward_from.id}')
          ], message.caption)
    else:
        prefix = f"Отправлено от {user_name}{' (edited)' if edit else ''}\n"
        count_text = len(prefix)
        if (message.caption):
            count_text = count_text + len(message.caption)
        if (count_text >= 1024):
            return message.caption, message.caption_entities
        result_text, result_entities = formating(prefix, message.caption_entities, [
          MessageEntity(type="blockquote", offset=0, length=14 + len(user_name) + 1 + (9 if edit else 0)),
          MessageEntity(type="text_link", offset=0, length=14 + len(user_name) + 1,
                        url=f'tg://user?id={message.from_user.id}')], message.caption)
    return result_text, result_entities