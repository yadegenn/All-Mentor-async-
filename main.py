from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import InputMediaType
from aiogram.filters import Command
from aiogram.types import Message, InputMediaPhoto
from pyrogram.types import InputMediaVideo

from middlewares.album import AlbumMiddleware

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
BOT_TOKEN = '6793024214:AAEk7_zBfBUbQfkByDSHAUauM-VPdSod6pg'
TARGET_CHAT_ID = -1002365612235
TARGET_THREAD_ID = 130

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(AlbumMiddleware())


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Отправь мне альбом, и я перешлю его в указанную группу.")

@dp.message(F.media_group_id)
async def media_handler(message: Message, album: list = None):
    if album:
        count_photos = len(album)
        media = []
        for i in album:
            if(i.photo):
                media.append(InputMediaPhoto(type=InputMediaType.PHOTO, media=i.photo[-1].file_id))
            elif(i.video):
                print(i.video.thumbnail.file_id)
                media.append(InputMediaVideo(media=i.video.file_id))
        await message.answer_media_group(media)
    else:
        await message.reply("спасибо за фото")




async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())