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
        user_data = get_user_data(message.from_user.id)
        if not user_data:
            await message.answer("ℹ️ Сначала заполните профиль через /start")
            return

        logger.info(f"Generating nutrition plan for user: {user_data}")

        # Улучшенный промпт с четкой структурой
        prompt = (
            f"Составь детальный план питания на 2 дня для мужчины:\n"
            f"- Вес: {user_data['weight']} кг\n"
            f"- Рост: {user_data['height']} см\n"
            f"- Возраст: {user_data['age']} лет\n"
            f"- Цель: {user_data['goal']}\n\n"
            "Формат ответа (строго соблюдать):\n"
            "День 1\n"
            "Завтрак:\n"
            "Обед:\n"
            "Ужин:\n"
            "КБЖУ дня: X ккал | Б: Xг | Ж: Xг | У: Xг\n\n"
            "День 2\n"
            "(аналогично)\n\n"
            
        )

        # Отправляем сообщение о начале генерации
        processing_msg = await message.answer("🍳 Готовим ваш персональный план питания...")

        # Получаем ответ от GigaChat
        response = await giga.ask(prompt)
        if not response or 'choices' not in response:
            raise Exception("Не получили ответ от API")

        full_plan = response['choices'][0]['message']['content']
        
        # Удаляем сообщение о генерации
        await processing_msg.delete()

        # Разбиваем план на части по 4000 символов
        chunk_size = 4000
        chunks = [full_plan[i:i+chunk_size] for i in range(0, len(full_plan), chunk_size)]

        # Отправляем первую часть с заголовком
        header = (
            f"🍏 *ПЕРСОНАЛЬНЫЙ ПЛАН ПИТАНИЯ* 🍏\n\n"
            f"*Ваши параметры:*\n"
            f"- Вес: {user_data['weight']} кг\n"
            f"- Рост: {user_data['height']} см\n"
            f"- Возраст: {user_data['age']} лет\n"
            f"- Цель: {user_data['goal']}\n\n"
        )
        
        first_chunk = header + chunks[0]
        await message.answer(first_chunk, parse_mode="Markdown")

        # Отправляем остальные части (если есть)
        for chunk in chunks[1:]:
            await message.answer(chunk)

        # Добавляем финальные рекомендации
        await message.answer(
            "💡 *Рекомендации по набору массы:*\n"
            "1. Соблюдайте режим питания (5-6 приемов пищи в день)\n"
            "2. Пейте 2-3 литра воды ежедневно\n"
            "3. Комбинируйте питание с силовыми тренировками\n"
            "4. Постепенно увеличивайте калорийность на 100-200 ккал\n\n"
            "🔄 Для нового плана используйте команду /nutrition",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Ошибка генерации плана: {str(e)}", exc_info=True)
        await message.answer(
            "⚠️ Не удалось сгенерировать полный план. Попробуйте:\n"
            "1. Проверить данные профиля (/start)\n"
            "2. Подождать 5 минут\n"
            "3. Обратиться в поддержку"
        )

@dp.message(Command("generate_meal"))
async def generate_meal(message: types.Message):
    if not await check_user_profile(message.from_user.id):
        await message.answer("⚠️ Сначала заполните профиль через команду /start")
        return
        
    try:
        user_data = get_user_data(message.from_user.id)
        prompt = (
            f"Придумай рецепт блюда для:\n"
            f"- Вес: {user_data['weight']} кг\n"
            f"- Рост: {user_data['height']} см\n"
            f"- Возраст: {user_data['age']} лет\n"
            f"- Цель: {user_data['goal']}\n\n"
            f"Опиши:\n"
            f"1. Ингредиенты (точные количества)\n"
            f"2. Пошаговый рецепт\n"
            f"3. Пищевую ценность"
        )
        
        response = await giga.ask(prompt)
        meal_description = response['choices'][0]['message']['content']
        image_url = generate_meal_image(f"{user_data['goal']}: {meal_description[:80]}...")
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=image_url,
            caption=meal_description[:1000]
        )
    except Exception as e:
        logger.error(f"Meal generation error: {str(e)}")
        await message.answer("⚠️ Не удалось сгенерировать рецепт. Попробуйте позже.")

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