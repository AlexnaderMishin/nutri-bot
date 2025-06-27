from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOI_TOKEN, GIGACHAT_AUTH_KEY  # Добавляем импорт ключа
import asyncio

from utils.gigachat import get_nutrition_plan, GigaChatAPI  # Импортируем класс GigaChatAPI
from utils.kandinsky import generate_meal_image
from database import save_user, get_user_data  # Предполагаем, что эта функция существует

bot = Bot(token=BOI_TOKEN)
dp = Dispatcher()

# Инициализируем GigaChat API
giga_chat = GigaChatAPI()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Введи данные в формате: Имя/Рост/Вес/Возраст/Цель")

@dp.message()
async def handle_profile(message: types.Message):
    try:
        name, height, weight, age, goal = message.text.split('/')
        # Сохраняем пользователя в БД
        save_user(
            user_id=message.from_user.id,
            name=name,
            height=float(height),
            weight=float(weight),
            age=int(age),
            goal=goal
        )
        await message.answer(f"Профиль сохранён! Цель: {goal}")
    except Exception as e:
        print(f"Error: {e}")
        await message.answer("Ошибка! Используй формат: Имя/Рост/Вес/Возраст/Цель")

@dp.message(Command("nutrition"))
async def send_nutrition(message: types.Message):
    try:
        # Получаем данные пользователя из БД
        user_data = get_user_data(message.from_user.id)
        if not user_data:
            await message.answer("Сначала заполните ваш профиль через команду /start")
            return
            
        # Формируем запрос к GigaChat
        prompt = (f"Создай план питания для: "
                 f"вес {user_data['weight']} кг, "
                 f"рост {user_data['height']} см, "
                 f"возраст {user_data['age']} лет, "
                 f"цель: {user_data['goal']}. "
                 f"Предоставь подробный план на день с калориями.")
        
        # Получаем ответ от GigaChat
        response = await giga_chat.ask_question(prompt)
        await message.answer(response)
        
    except Exception as e:
        print(f"Error in nutrition command: {e}")
        await message.answer("Произошла ошибка при генерации плана питания")

@dp.message(Command("generate_meal"))
async def generate_meal(message: types.Message):
    try:
        user_data = get_user_data(message.from_user.id)
        if not user_data:
            await message.answer("Сначала заполните ваш профиль через команду /start")
            return
            
        prompt = (f"Идея для блюда подходящего для: "
                 f"вес {user_data['weight']} кг, "
                 f"рост {user_data['height']} см, "
                 f"возраст {user_data['age']} лет, "
                 f"цель: {user_data['goal']}")
        
        # Получаем описание блюда от GigaChat
        meal_description = await giga_chat.ask_question(prompt)
        
        # Генерируем изображение
        image_url = generate_meal_image(meal_description)
        await bot.send_photo(message.chat.id, image_url, caption=meal_description)
        
    except Exception as e:
        print(f"Error in generate_meal command: {e}")
        await message.answer("Произошла ошибка при генерации блюда")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())