import aiohttp

from telebot.async_telebot import AsyncTeleBot


TOKEN = '6793024214:AAEk7_zBfBUbQfkByDSHAUauM-VPdSod6pg'
proxy_url = 'http://RQdzNw:zxCVvm@194.41.56.95:8000'  # пример прокси

session = aiohttp.ClientSession()
bot = AsyncTeleBot(TOKEN)