from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
import asyncio

from utils.gigachat import get_nutrition_plan, GigaChatAPI  # Добавляем импорт GigaChatAPI
from utils.kandinsky import generate_meal_image
from database import save_user, get_user_data  # Предполагаем, что эта функция существует

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализируем GigaChat API
giga = GigaChatAPI()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Введи данные в формате: Имя/Рост/Вес/Возраст/Цель\n"
                       "Также доступны команды:\n"
                       "/nutrition - получить план питания\n"
                       "/generate_meal - сгенерировать блюдо\n"
                       "/ask [вопрос] - задать вопрос GigaChat")

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
    except:
        await message.answer("Ошибка! Используй формат: Имя/Рост/Вес/Возраст/Цель")

@dp.message(Command("nutrition"))
async def send_nutrition(message: types.Message):
    try:
        user_data = get_user_data(message.from_user.id)
        if not user_data:
            await message.answer("Сначала заполните ваш профиль через команду /start")
            return
            
        prompt = (f"Создай план питания для:\n"
                 f"Вес: {user_data['weight']} кг\n"
                 f"Рост: {user_data['height']} см\n"
                 f"Возраст: {user_data['age']} лет\n"
                 f"Цель: {user_data['goal']}\n"
                 f"Предоставь подробный план на день с калориями.")
        
        response = await giga.ask(prompt)
        await message.answer(response['choices'][0]['message']['content'][:4000])
    except Exception as e:
        await message.answer(f"Ошибка при генерации плана: {str(e)}")

@dp.message(Command("generate_meal"))
async def generate_meal(message: types.Message):
    try:
        user_data = get_user_data(message.from_user.id)
        if not user_data:
            await message.answer("Сначала заполните ваш профиль через команду /start")
            return
            
        prompt = (f"Придумай рецепт блюда для:\n"
                 f"Вес: {user_data['weight']} кг\n"
                 f"Рост: {user_data['height']} см\n"
                 f"Возраст: {user_data['age']} лет\n"
                 f"Цель: {user_data['goal']}\n"
                 f"Опиши подробно рецепт и ингредиенты.")
        
        response = await giga.ask(prompt)
        meal_description = response['choices'][0]['message']['content']
        image_url = generate_meal_image(meal_description[:100])  # Первые 100 символов как промпт для изображения
        await bot.send_photo(message.chat.id, image_url, caption=meal_description[:1000])
    except Exception as e:
        await message.answer(f"Ошибка при генерации блюда: {str(e)}")

@dp.message(Command("ask"))
async def handle_gigachat(message: types.Message):
    try:
        # Получаем текст после команды /ask
        question = message.text[5:].strip()
        if not question:
            await message.answer("Введите вопрос после команды /ask")
            return
            
        response = await giga.ask(question)
        answer = response['choices'][0]['message']['content']
        await message.answer(answer[:4000])  # Обрезаем длинные ответы
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
# from aiogram import Bot, Dispatcher, types
# from aiogram.filters import Command
# from config import BOT_TOKEN
# import asyncio

# from utils.gigachat import get_nutrition_plan
# from utils.kandinsky import generate_meal_image
# from database import save_user

# bot = Bot(token=BOT_TOKEN)
# dp = Dispatcher()

# @dp.message(Command("start"))
# async def start(message: types.Message):
#     await message.answer("Привет! Введи данные в формате: Имя/Рост/Вес/Возраст/Цель")

# @dp.message()
# async def handle_profile(message: types.Message):
#     try:
#         name, height, weight, age, goal = message.text.split('/')
#         await message.answer(f"Профиль сохранён! Цель: {goal}")
#     except:
#         await message.answer("Ошибка! Используй формат: Имя/Рост/Вес/Возраст/Цель")

# async def main():
#     await dp.start_polling(bot)

# if __name__ == "__main__":
#     asyncio.run(main())

# @dp.message(Command("nutrition"))
# async def send_nutrition(message: types.Message):
#     user_data = get_user_data(message.from_user.id)  # Функция для получения данных из БД
#     plan = get_nutrition_plan(user_data["weight"], user_data["height"], user_data["age"], user_data["goal"])
#     await message.answer(plan)

# @dp.message(Command("generate_meal"))
# async def generate_meal(message: types.Message):
#     image_url = generate_meal_image("Здоровый завтрак для похудения")
#     await bot.send_photo(message.chat.id, image_url)

