from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import save_food_entry, get_today_food_entries
from config import BOT_TOKEN
import asyncio
import logging
import datetime

from database import save_user, get_user_data

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
router = Router()

def get_commands_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/profile"), KeyboardButton(text="/update")],
            [KeyboardButton(text="/food_diary"), KeyboardButton(text="/help")]  # Добавлено
        ],
        resize_keyboard=True
    )

async def check_user_profile(user_id: int) -> bool:
    return get_user_data(user_id) is not None

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        f"👋 <b>Добро пожаловать!</b>\n\n"
        f"📅 Сегодня: {datetime.datetime.now().strftime('%d.%m.%Y')}\n\n"
    )
    
    if not await check_user_profile(message.from_user.id):
        await message.answer(
            welcome_text +
            "Я помогу вам отслеживать ваши параметры.\n"
            "Введите данные в формате:\n"
            "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
            "Пример: <code>Александр / 180 / 75 / 30 / похудение</code>",
            parse_mode="HTML"
        )
    else:
        user_data = get_user_data(message.from_user.id)
        await message.answer(
            welcome_text +
            f"Ваш профиль уже заполнен. Используйте команды ниже 👇",
            reply_markup=get_commands_keyboard(),
            parse_mode="HTML"
        )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "ℹ️ <b>Доступные команды:</b>\n\n"
        "/profile - Показать ваш профиль\n"
        "/update - Обновить данные\n"
        "/help - Показать это сообщение\n\n"
        "Для ввода данных используйте формат:\n"
        "<code>Имя / Рост / Вес / Возраст / Цель</code>",
        reply_markup=get_commands_keyboard(),
        parse_mode="HTML"
    )


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
        reply_markup=get_commands_keyboard(),
        parse_mode="HTML"
    )

@router.message(lambda message: len(message.text.split('/')) == 5)
async def handle_food_entry(message: types.Message):
    try:
        food_name, calories, protein, fats, carbs = [x.strip() for x in message.text.split('/')]
        save_food_entry(
            user_id=message.from_user.id,  # Исправлено: = вместо -
            food_name=food_name,
            calories=int(calories),
            protein=float(protein),
            fats=float(fats),
            carbs=float(carbs)
        )
        await message.answer("✅ Запись о еде добавлена!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")  # Исправлено: нормальная обработка ошибки

@router.message(Command("food_diary"))  # Исправлено: правильный декоратор
async def show_food_diary(message: types.Message):
    entries = get_today_food_entries(message.from_user.id)
    if not entries:
        await message.answer("Сегодня вы еще ничего не ели.")
        return
    
    text = "🍽 <b>Ваш дневник питания:</b>\n\n"
    for entry in entries:
        text += (
            f"• {entry.food_name}: "
            f"{entry.calories} ккал, "
            f"Б: {entry.protein}g, Ж: {entry.fats}g, У: {entry.carbs}g\n"
        )
    await message.answer(text, parse_mode="HTML")  # Добавлено завершение функции


@router.message(Command("update"))
async def update_profile(message: types.Message):
    await message.answer(
        "✏️ Введите новые данные в формате:\n"
        "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
        "Пример: <code>Александр / 180 / 75 / 30 / похудение</code>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )

@router.message(F.text == "Отмена")
async def cancel_update(message: types.Message):
    await message.answer("Действие отменено", reply_markup=get_commands_keyboard())

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
            "✅ <b>Данные успешно сохранены!</b>",
            reply_markup=get_commands_keyboard(),
            parse_mode="HTML"
        )
        await show_profile(message)
    except ValueError as e:
        await message.answer(
            f"❌ <b>Ошибка:</b> {str(e)}\n\n"
            "Правильный формат:\n"
            "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
            "Пример: <code>Иван / 180 / 75 / 30 / похудение</code>",
            reply_markup=get_commands_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения: {str(e)}")
        await message.answer(
            "❌ <b>Ошибка при сохранении данных</b>",
            reply_markup=get_commands_keyboard(),
            parse_mode="HTML"
        )

@router.message()
async def handle_unknown(message: types.Message):
    if await check_user_profile(message.from_user.id):
        await message.answer(
            "Используйте команды ниже 👇",
            reply_markup=get_commands_keyboard()
        )
    else:
        await message.answer(
            "Сначала заполните профиль. Введите данные в формате:\n"
            "<b>Имя / Рост / Вес / Возраст / Цель</b>",
            parse_mode="HTML"
        )

async def main():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())