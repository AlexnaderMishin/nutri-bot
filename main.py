from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from config import BOT_TOKEN
import asyncio
import logging

from utils.gigachat import GigaChatAPI
from utils.kandinsky import generate_meal_image
from database import save_user, get_user_data

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
giga = GigaChatAPI()

async def check_user_profile(user_id: int) -> bool:
    """Проверяет, заполнен ли профиль пользователя"""
    user_data = get_user_data(user_id)
    return user_data is not None

@dp.message(Command("start"))
async def start(message: types.Message):
    if await check_user_profile(message.from_user.id):
        user_data = get_user_data(message.from_user.id)
        await message.answer(
            f"Ваш профиль уже заполнен:\n"
            f"Имя: {user_data['name']}\n"
            f"Рост: {user_data['height']} см\n"
            f"Вес: {user_data['weight']} кг\n"
            f"Возраст: {user_data['age']} лет\n"
            f"Цель: {user_data['goal']}\n\n"
            "Доступные команды:\n"
            "/nutrition - получить план питания\n"
            "/generate_meal - сгенерировать блюдо\n"
            "/ask [вопрос] - задать вопрос GigaChat\n"
            "/update - обновить данные профиля"
        )
    else:
        await message.answer(
            "Привет! Введи данные в формате: Имя/Рост/Вес/Возраст/Цель\n"
            "Пример: Александр/180/75/30/похудение"
        )

@dp.message(Command("update"))
async def update_profile(message: types.Message):
    await message.answer("Введите новые данные в формате: Имя/Рост/Вес/Возраст/Цель")

@dp.message(lambda message: len(message.text.split('/')) == 5)
async def handle_profile(message: types.Message):
    try:
        name, height, weight, age, goal = message.text.split('/')
        
        # Валидация данных
        if not all([name.strip(), height.strip(), weight.strip(), age.strip(), goal.strip()]):
            raise ValueError("Все поля должны быть заполнены")
            
        height_val = float(height)
        weight_val = float(weight)
        age_val = int(age)
        
        if height_val <= 0 or weight_val <= 0 or age_val <= 0:
            raise ValueError("Значения должны быть положительными")
        
        save_user(
            user_id=message.from_user.id,
            name=name.strip(),
            height=height_val,
            weight=weight_val,
            age=age_val,
            goal=goal.strip()
        )
        await message.answer(f"✅ Профиль сохранён!\nИмя: {name}\nРост: {height} см\nВес: {weight} кг\nВозраст: {age} лет\nЦель: {goal}")
    except ValueError as e:
        await message.answer(f"❌ Ошибка в данных: {str(e)}\nИспользуй формат: Имя/Рост/Вес/Возраст/Цель\nПример: Иван/180/75/30/похудение")
    except Exception as e:
        logger.error(f"Error saving profile: {str(e)}")
        await message.answer("❌ Произошла ошибка при сохранении профиля")

@dp.message(Command("nutrition"))
async def send_nutrition(message: types.Message):
    try:
        # Проверяем профиль пользователя
        if not await check_user_profile(message.from_user.id):
            await message.answer("ℹ️ Сначала заполните профиль через /start")
            return

        user_data = get_user_data(message.from_user.id)
        logger.info(f"Generating nutrition plan for user: {user_data}")

        # Улучшенный промпт с четкой структурой
        prompt = f"""
        Составь детальный план питания на 1 день для мужчины:
        - Вес: {user_data['weight']} кг
        - Рост: {user_data['height']} см
        - Возраст: {user_data['age']} лет
        - Цель: {user_data['goal']}
        
        Формат ответа (строго соблюдать):
        === Калорийность ===
        XXXX ккал/день
        
        === БЖУ ===
        Белки: XXг (X.Xг/кг)
        Жиры: XXг
        Углеводы: XXг
        
        === Меню ===
        Завтрак:
        - Блюдо 1 (XX г) - XX ккал
        - Блюдо 2 (XX г) - XX ккал
        
        Обед:
        - Блюдо 1 (XX г) - XX ккал
        - Блюдо 2 (XX г) - XX ккал
        
        Ужин:
        - Блюдо 1 (XX г) - XX ккал
        - Блюдо 2 (XX г) - XX ккал
        
        Перекусы:
        - Перекус 1 (XX г) - XX ккал
        """

        # Добавляем индикатор загрузки
        processing_msg = await message.answer("🍳 Готовим ваш персональный план питания...")

        # Получаем ответ от GigaChat
        try:
            response = await giga.ask(prompt)
            if not response or 'choices' not in response:
                raise Exception("Не получили корректный ответ от API")
            
            plan = response['choices'][0]['message']['content']
            
            # Проверяем минимальную длину ответа
            if len(plan) < 100:
                raise Exception("Ответ слишком короткий")
            
            await processing_msg.delete()
            await message.answer(plan[:4000], parse_mode="Markdown")
            
        except Exception as e:
            await processing_msg.delete()
            logger.error(f"GigaChat error: {str(e)}")
            await message.answer("⚠️ Ошибка при обращении к GigaChat API. Попробуйте позже.")

    except Exception as e:
        logger.error(f"Nutrition error: {str(e)}")
        await message.answer("⚠️ Внутренняя ошибка при генерации плана. Попробуйте позже.")

@dp.message(Command("ask"))
async def handle_gigachat(message: types.Message):
    try:
        question = message.text[4:].strip()  # Убираем "/ask "
        if not question:
            await message.answer("Введите вопрос после команды /ask")
            return
            
        response = await giga.ask(question)
        answer = response['choices'][0]['message']['content']
        await message.answer(answer[:4000])
    except Exception as e:
        logger.error(f"GigaChat error: {str(e)}")
        await message.answer("⚠️ Не удалось получить ответ. Попробуйте позже.")

@dp.message()
async def handle_unknown(message: types.Message):
    if await check_user_profile(message.from_user.id):
        await message.answer("Неизвестная команда. Используйте /nutrition, /generate_meal или /ask")
    else:
        await message.answer("Сначала заполните профиль через /start")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
