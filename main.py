from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import BOT_TOKEN
import asyncio
import logging

from database import save_user, get_user_data

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
router = Router()

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="✏️ Обновить")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

async def check_user_profile(user_id: int) -> bool:
    return get_user_data(user_id) is not None

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if await check_user_profile(message.from_user.id):
        user_data = get_user_data(message.from_user.id)
        await message.answer(
            "Добро пожаловать! Вот ваши данные:\n"
            f"Имя: {user_data['name']}\n"
            f"Рост: {user_data['height']} см\n"
            f"Вес: {user_data['weight']} кг\n"
            f"Возраст: {user_data['age']} лет\n"
            f"Цель: {user_data['goal']}",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Привет! Для начала введите свои данные в формате:\n"
            "<b>Имя/Рост/Вес/Возраст/Цель</b>\n\n"
            "Пример: <code>Александр/180/75/30/похудение</code>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

@router.message(F.text == "❓ Помощь")
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "ℹ️ <b>Доступные команды:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/profile - Показать ваш профиль\n"
        "/update - Обновить данные профиля\n"
        "/help - Показать это сообщение\n\n"
        "Или используйте кнопки ниже 👇",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "👤 Профиль")
@router.message(Command("profile"))
async def show_profile(message: types.Message):
    if not await check_user_profile(message.from_user.id):
        await message.answer("Профиль не заполнен. Введите данные через /start")
        return
    
    user_data = get_user_data(message.from_user.id)
    await message.answer(
        "📋 <b>Ваш профиль:</b>\n\n"
        f"👤 Имя: {user_data['name']}\n"
        f"📏 Рост: {user_data['height']} см\n"
        f"⚖️ Вес: {user_data['weight']} кг\n"
        f"🎂 Возраст: {user_data['age']} лет\n"
        f"🎯 Цель: {user_data['goal']}",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "✏️ Обновить")
@router.message(Command("update"))
async def update_profile(message: types.Message):
    await message.answer(
        "✏️ Введите новые данные в формате:\n"
        "<b>Имя/Рост/Вес/Возраст/Цель</b>\n\n"
        "Пример: <code>Александр/180/75/30/похудение</code>\n\n"
        "Для отмены введите любой текст",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

@router.message(lambda message: len(message.text.split('/')) == 5)
async def handle_profile_data(message: types.Message):
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
        await message.answer(
            "✅ <b>Профиль успешно сохранён!</b>",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        await show_profile(message)
    except ValueError as e:
        await message.answer(
            f"❌ <b>Ошибка:</b> {str(e)}\n\n"
            "Правильный формат: <b>Имя/Рост/Вес/Возраст/Цель</b>\n\n"
            "Пример: <code>Иван/180/75/30/похудение</code>",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения: {str(e)}")
        await message.answer(
            "❌ <b>Произошла ошибка при сохранении профиля</b>",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )

@router.message()
async def handle_other_messages(message: types.Message):
    if await check_user_profile(message.from_user.id):
        await message.answer(
            "Я не понимаю эту команду. Используйте кнопки ниже 👇",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Сначала заполните профиль через /start",
            reply_markup=ReplyKeyboardRemove()
        )

async def main():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())