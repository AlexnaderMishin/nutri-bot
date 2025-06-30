from aiogram import Bot, Dispatcher, types, Router
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
router = Router()

def get_botfather_style_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/start")],
            [KeyboardButton(text="/profile")],
            [KeyboardButton(text="/update")],
            [KeyboardButton(text="/help")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите команду..."
    )

async def check_user_profile(user_id: int) -> bool:
    return get_user_data(user_id) is not None

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if not await check_user_profile(message.from_user.id):
        await message.answer(
            "Привет! Введи данные в формате:\n"
            "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
            "Пример: <code>Александр / 180 / 75 / 30 / похудение</code>",
            parse_mode="HTML",
            reply_markup=get_botfather_style_menu()
        )
    else:
        user_data = get_user_data(message.from_user.id)
        await message.answer(
            "✅ Профиль уже заполнен. Доступные команды:",
            reply_markup=get_botfather_style_menu()
        )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📜 <b>Список команд:</b>\n\n"
        "/start - Начать работу\n"
        "/profile - Показать профиль\n"
        "/update - Обновить данные\n"
        "/help - Эта справка",
        parse_mode="HTML",
        reply_markup=get_botfather_style_menu()
    )

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    if not await check_user_profile(message.from_user.id):
        await message.answer("Сначала заполните профиль через /start")
        return
    
    user_data = get_user_data(message.from_user.id)
    await message.answer(
        "📋 <b>Ваш профиль:</b>\n\n"
        f"👤 Имя: {user_data['name']}\n"
        f"📏 Рост: {user_data['height']} см\n"
        f"⚖️ Вес: {user_data['weight']} кг\n"
        f"🎂 Возраст: {user_data['age']} лет\n"
        f"🎯 Цель: {user_data['goal']}",
        parse_mode="HTML",
        reply_markup=get_botfather_style_menu()
    )

@router.message(Command("update"))
async def cmd_update(message: types.Message):
    await message.answer(
        "Введите новые данные в формате:\n"
        "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
        "Для отмены просто введите любой текст",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]],
            resize_keyboard=True
        )
    )

@router.message(lambda message: len(message.text.split('/')) == 5)
async def handle_profile_data(message: types.Message):
    try:
        name, height, weight, age, goal = [x.strip() for x in message.text.split('/')]
        
        if not all([name, height, weight, age, goal]):
            raise ValueError("Все поля должны быть заполнены")
            
        height_val = float(height)
        weight_val = float(weight)
        age_val = int(age)
        
        if height_val <= 0 or weight_val <= 0 or age_val <= 0:
            raise ValueError("Значения должны быть положительными")
        
        save_user(
            user_id=message.from_user.id,
            name=name,
            height=height_val,
            weight=weight_val,
            age=age_val,
            goal=goal
        )
        await message.answer(
            "✅ Данные сохранены!",
            reply_markup=get_botfather_style_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\n"
            "Используйте формат:\n"
            "<b>Имя / Рост / Вес / Возраст / Цель</b>",
            parse_mode="HTML",
            reply_markup=get_botfather_style_menu()
        )

async def main():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())