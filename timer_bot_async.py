
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot import asyncio_filters, State
from telebot.states.asyncio import StateContext, StateMiddleware

# Инициализация бота с StateMemoryStorage
state_storage = StateMemoryStorage()
bot = AsyncTeleBot('6793024214:AAEk7_zBfBUbQfkByDSHAUauM-VPdSod6pg', state_storage=state_storage)


# Определение состояний
class UserStates:
    name = State()
    age = State()


# Обработчик команды /start
@bot.message_handler(commands=['start'])
async def start_ex(message, state: StateContext):
    await state.set(UserStates.name)
    await bot.send_message(message.chat.id, "Привет! Как тебя зовут?")


# Обработчик для получения имени
@bot.message_handler(state=UserStates.name)
async def get_name(message):
    print("лол")
    await bot.send_message(message.chat.id, f"Приятно познакомиться, {message.text}! Сколько тебе лет?")
    await bot.set_state(message.from_user.id, UserStates.age, message.chat.id)
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['name'] = message.text


# Обработчик для получения возраста
@bot.message_handler(state=UserStates.age)
async def get_age(message):
    if not message.text.isdigit():
        await bot.send_message(message.chat.id, "Пожалуйста, введите число.")
        return

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        name = data.get('name', 'Пользователь')
        await bot.send_message(message.chat.id, f"Отлично, {name}! Тебе {message.text} лет.")
    await bot.delete_state(message.from_user.id, message.chat.id)


# Обработчик для отмены текущего состояния
@bot.message_handler(commands=['cancel'])
async def cancel_state(message):
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.send_message(message.chat.id, "Текущая операция отменена.")


# Функция для запуска бота
async def main():
    # Регистрация фильтров состояний
    bot.add_custom_filter(asyncio_filters.StateFilter(bot))
    bot.add_custom_filter(asyncio_filters.IsDigitFilter())
    bot.setup_middleware(StateMiddleware(bot))
    await bot.polling(non_stop=True, interval=0)


if __name__ == '__main__':
    asyncio.run(main())