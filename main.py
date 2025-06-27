from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
import asyncio

from utils.gigachat import get_nutrition_plan
from utils.kandinsky import generate_meal_image
from database import save_user

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Введи данные в формате: Имя/Рост/Вес/Возраст/Цель")

@dp.message()
async def handle_profile(message: types.Message):
    try:
        name, height, weight, age, goal = message.text.split('/')
        await message.answer(f"Профиль сохранён! Цель: {goal}")
    except:
        await message.answer("Ошибка! Используй формат: Имя/Рост/Вес/Возраст/Цель")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

@dp.message(Command("nutrition"))
async def send_nutrition(message: types.Message):
    user_data = get_user_data(message.from_user.id)  # Функция для получения данных из БД
    plan = get_nutrition_plan(user_data["weight"], user_data["height"], user_data["age"], user_data["goal"])
    await message.answer(plan)

@dp.message(Command("generate_meal"))
async def generate_meal(message: types.Message):
    image_url = generate_meal_image("Здоровый завтрак для похудения")
    await bot.send_photo(message.chat.id, image_url)