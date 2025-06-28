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
            "/test_giga - обновить данные профиля"
            "/show_config - обновить данные профиля"
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
        # Правильные отступы (используйте 4 пробела)
        user_data = get_user_data(message.from_user.id)
        if not user_data:
            await message.answer("⚠️ Сначала заполните профиль через /start")
            return
            
        # Формируем правильный промпт для GigaChat
        prompt = (
            f"Создай детальный план питания для:\n"
            f"- Вес: {user_data['weight']} кг\n"
            f"- Рост: {user_data['height']} см\n"
            f"- Возраст: {user_data['age']} лет\n"
            f"- Цель: {user_data['goal']}\n\n"
            "Предоставь в формате:\n"
            "1. Рекомендуемая калорийность\n"
            "2. Баланс БЖУ\n"
            "3. Пример меню на день с разбивкой по приемам пищи"
        )
        
        response = await giga.ask(prompt)
        plan = response['choices'][0]['message']['content']
        
        # Форматируем ответ (исправлены кавычки и скобки)
        formatted_plan = (
            "🍎 *Персональный план питания* 🍎\n\n"
            "🔹 *Параметры:*\n"
            f"• Вес: {user_data['weight']} кг\n"
            f"• Рост: {user_data['height']} см\n"
            f"• Возраст: {user_data['age']} лет\n"
            f"• Цель: {user_data['goal']}\n\n"
            "📊 *Рекомендации:*\n"
            "```\n"
            f"{self._extract_section(plan, 'Рекомендуемая калорийность')}\n"
            "```\n\n"
            "🍽️ *Пример меню на день:*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🍳 *Завтрак:*\n"
            f"{self._format_meal(plan, 'Завтрак')}\n\n"
            "☕ *Перекус:*\n"
            f"{self._format_meal(plan, 'Перекус')}\n\n"
            "🍗 *Обед:*\n"
            f"{self._format_meal(plan, 'Обед')}\n\n"
            "🥗 *Ужин:*\n"
            f"{self._format_meal(plan, 'Ужин')}\n\n"
            "💧 *Совет:* Не забывайте пить воду!"
        )
        
        await message.answer(
            formatted_plan,
            parse_mode="MarkdownV2",  # Используем MarkdownV2 для лучшей поддержки
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Error generating nutrition plan: {str(e)}")
        await message.answer("⚠️ Не удалось сгенерировать план питания. Попробуйте позже.")

def _format_meal(self, plan: str, meal_type: str) -> str:
    """Форматирует описание приема пищи"""
    parts = plan.split(f"{meal_type}:")
    if len(parts) > 1:
        meal = parts[1].split("\n\n")[0].strip()
        return "• " + meal.replace("\n", "\n• ")
    return "• Информация отсутствует"

def _extract_section(self, text: str, section_name: str) -> str:
    """Извлекает конкретную секцию из текста"""
    if section_name in text:
        return text.split(section_name)[1].split("\n\n")[0].strip()
    return "Данные не найдены"

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

@dp.message(Command("show_config"))
async def show_config(message: types.Message):
    from config import BOT_TOKEN, GIGACHAT_AUTH_KEY, DATABASE_URL
    config_info = (
        f"Конфигурация:\n"
        f"BOT_TOKEN: {'установлен' if BOT_TOKEN else 'НЕ НАЙДЕН'}\n"
        f"GIGACHAT_AUTH_KEY: {'установлен' if GIGACHAT_AUTH_KEY else 'НЕ НАЙДЕН'}\n"
        f"DATABASE_URL: {'установлен' if DATABASE_URL else 'НЕ НАЙДЕН'}"
    )
    await message.answer(config_info)

@dp.message(Command("test_giga"))
async def test_giga(message: types.Message):
    try:
        # Простейший тестовый запрос
        test_prompt = "Ответь одним словом: работаю"
        response = await giga.ask(test_prompt)
        
        if response:
            answer = response['choices'][0]['message']['content']
            await message.answer(f"✅ GigaChat отвечает: {answer}")
        else:
            await message.answer("❌ Получен пустой ответ от GigaChat")
            
    except Exception as e:
        error_msg = f"❌ Ошибка подключения к GigaChat:\n{str(e)}"
        logger.error(error_msg)
        await message.answer(error_msg)

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
