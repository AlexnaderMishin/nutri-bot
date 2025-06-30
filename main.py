from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN
import asyncio
import logging

from database import save_user, get_user_data

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

def get_main_keyboard():
    buttons = [
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="✏️ Обновить данные")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

async def check_user_profile(user_id: int) -> bool:
    """Проверяет, заполнен ли профиль пользователя"""
    return get_user_data(user_id) is not None

@router.message(Command("start") | F.text == "❓ Помощь")
async def start(message: types.Message):
    if await check_user_profile(message.from_user.id):
        user_data = get_user_data(message.from_user.id)
        await message.answer(
            "Доступные команды:\n"
            "👤 Профиль - показать ваш профиль\n"
            "✏️ Обновить данные - изменить параметры\n\n"
            f"Текущие данные:\n"
            f"Имя: {user_data['name']}\n"
            f"Рост: {user_data['height']} см\n"
            f"Вес: {user_data['weight']} кг\n"
            f"Возраст: {user_data['age']} лет\n"
            f"Цель: {user_data['goal']}",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Привет! Для начала работы введи данные в формате:\n"
            "Имя/Рост/Вес/Возраст/Цель\n\n"
            "Пример: Александр/180/75/30/похудение",
            reply_markup=get_main_keyboard()
        )

@router.message(Command("profile") | F.text == "👤 Профиль")
async def show_profile(message: types.Message):
    if not await check_user_profile(message.from_user.id):
        await message.answer("Профиль не заполнен. Введите данные в формате: Имя/Рост/Вес/Возраст/Цель", 
                           reply_markup=get_main_keyboard())
        return
    
    user_data = get_user_data(message.from_user.id)
    await message.answer(
        f"Ваш профиль:\n"
        f"Имя: {user_data['name']}\n"
        f"Рост: {user_data['height']} см\n"
        f"Вес: {user_data['weight']} кг\n"
        f"Возраст: {user_data['age']} лет\n"
        f"Цель: {user_data['goal']}",
        reply_markup=get_main_keyboard()
    )

@router.message(Command("update") | F.text == "✏️ Обновить данные")
async def update_profile(message: types.Message):
    await message.answer(
        "Введите новые данные в формате: Имя/Рост/Вес/Возраст/Цель\n\n"
        "Пример: Александр/180/75/30/похудение\n\n"
        "Для отмены нажмите кнопку ниже",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )

@router.message(F.text == "❌ Отмена")
async def cancel_update(message: types.Message):
    await message.answer("Обновление отменено", reply_markup=get_main_keyboard())

@router.message(lambda message: len(message.text.split('/')) == 5)
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
        await message.answer("✅ Профиль сохранён!", reply_markup=get_main_keyboard())
        await show_profile(message)
    except ValueError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\n"
            "Правильный формат: Имя/Рост/Вес/Возраст/Цель\n\n"
            "Пример: Иван/180/75/30/похудение",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения: {str(e)}")
        await message.answer("❌ Произошла ошибка при сохранении профиля", reply_markup=get_main_keyboard())

@router.message()
async def handle_unknown(message: types.Message):
    await message.answer(
        "Я не понимаю эту команду. Используйте кнопки ниже 👇",
        reply_markup=get_main_keyboard()
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())