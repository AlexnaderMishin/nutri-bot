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
        # Проверяем заполненность профиля
        if not await check_user_profile(message.from_user.id):
            await message.answer("ℹ️ Сначала заполните профиль через /start")
            return

        user_data = get_user_data(message.from_user.id)
        logger.info(f"Generating nutrition plan for user: {user_data}")

        # Оптимизированный промпт с четкой структурой
        prompt = (
            f"Составь примерный план питания на 3 дня для мужчины с указанными параметрами. "
    f"Это общие рекомендации, а не медицинское назначение.\n\n"
    f"Параметры:\n"
    f"- Вес: {user_data['weight']} кг\n"
    f"- Рост: {user_data['height']} см\n"
    f"- Возраст: {user_data['age']} лет\n"
    f"- Цель: {user_data['goal']}\n\n"
    "Формат ответа:\n"
    "=== День 1 ===\n"
    "**Завтрак:**\n"
    "- Овсяная каша на молоке (50г овсянки + 150мл молока)\n"
    "- 2 яйца вареных\n"
    "- 30г орехов\n\n"
    "**Обед:**\n"
    "- 150г куриной грудки\n"
    "- 100г гречки (сухой вес)\n"
    "- 200г овощного салата\n\n"
    "**Ужин:**\n"
    "- 200г запеченной рыбы\n"
    "- 150г бурого риса\n"
    "- 100г тушеных овощей\n\n"
    "**КБЖУ дня:** ~2500 ккал | Б: 180г | Ж: 90г | У: 250г\n\n"
    "=== День 2 ===\n"
    "(аналогичный формат)\n\n"
    "Важно: Это примерный план. Для персонализированных рекомендаций обратитесь к диетологу."
        )

        # Добавляем индикатор отправки запроса
        processing_msg = await message.answer("⌛ Генерируем ваш персональный план питания...")

        # Запрос с таймаутом
        try:
            response = await asyncio.wait_for(
                giga.ask(prompt),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            await processing_msg.delete()
            await message.answer("⌛ Время ожидания истекло. Попробуйте позже.")
            return

        if not response or 'choices' not in response:
            await processing_msg.delete()
            raise Exception("Не получили корректный ответ от API")

        plan = response['choices'][0]['message']['content']
        
        # Проверка минимальной длины ответа
        if len(plan) < 100:
            await processing_msg.delete()
            raise Exception("Ответ слишком короткий")

        # Разбиваем на части если превышает лимит
        chunks = [plan[i:i+4000] for i in range(0, len(plan), 4000)]
        
        await processing_msg.delete()
        
        # Отправляем первую часть с заголовком
        header = (
            f"🍏 *ПЛАН ПИТАНИЯ* 🍏\n\n"
            f"*Параметры:*\n"
            f"- Вес: {user_data['weight']} кг\n"
            f"- Рост: {user_data['height']} см\n"
            f"- Возраст: {user_data['age']} лет\n"
            f"- Цель: {user_data['goal']}\n\n"
        )
        
        first_chunk = header + chunks[0]
        await message.answer(first_chunk, parse_mode="Markdown")
        
        # Отправляем остальные части
        for chunk in chunks[1:]:
            await message.answer(chunk)
            
        # Финальные рекомендации
        await message.answer(
            "💡 *Рекомендации:*\n"
            "1. Пейте 2-3 литра воды в день\n"
            "2. Соблюдайте режим питания\n"
            "3. Адаптируйте план под свои предпочтения\n\n"
            "🔄 Для нового плана используйте /nutrition",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Ошибка генерации плана: {str(e)}", exc_info=True)
        error_msg = (
            "⚠️ *Не удалось сгенерировать план*\n\n"
            "Попробуйте:\n"
            "1. Проверить данные профиля (/start)\n"
            "2. Использовать более простой запрос\n"
            "3. Подождать 5 минут и попробовать снова\n\n"
            "Если проблема сохраняется, обратитесь в поддержку"
        )
        await message.answer(error_msg, parse_mode="Markdown")

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