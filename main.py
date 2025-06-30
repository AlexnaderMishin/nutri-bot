from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN
import asyncio
import logging

from database import save_user, get_user_data

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
router = Router()

def get_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
            [InlineKeyboardButton(text="✏️ Обновить данные", callback_data="update")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
        ]
    )

async def check_user_profile(user_id: int) -> bool:
    return get_user_data(user_id) is not None

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if await check_user_profile(message.from_user.id):
        await message.answer(
            "🔹 <b>Главное меню</b> 🔹\n"
            "Выберите действие:",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "Привет! Для начала работы введите свои данные в формате:\n"
            "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
            "Пример: <code>Александр / 180 / 75 / 30 / похудение</code>",
            parse_mode="HTML"
        )

@router.callback_query(F.data == "help")
async def callback_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ <b>Справка по боту</b> ℹ️\n\n"
        "Этот бот помогает отслеживать ваши параметры:\n\n"
        "• <b>Мой профиль</b> - просмотр текущих данных\n"
        "• <b>Обновить данные</b> - изменение параметров\n\n"
        "Для ввода данных используйте формат:\n"
        "<code>Имя / Рост / Вес / Возраст / Цель</code>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "profile")
async def callback_profile(callback: types.CallbackQuery):
    if not await check_user_profile(callback.from_user.id):
        await callback.message.edit_text(
            "Профиль не заполнен. Введите данные через /start",
            reply_markup=get_main_menu()
        )
        return
    
    user_data = get_user_data(callback.from_user.id)
    await callback.message.edit_text(
        "📋 <b>Ваш профиль</b> 📋\n\n"
        f"👤 <b>Имя:</b> {user_data['name']}\n"
        f"📏 <b>Рост:</b> {user_data['height']} см\n"
        f"⚖️ <b>Вес:</b> {user_data['weight']} кг\n"
        f"🎂 <b>Возраст:</b> {user_data['age']} лет\n"
        f"🎯 <b>Цель:</b> {user_data['goal']}",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "update")
async def callback_update(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "✏️ <b>Обновление данных</b> ✏️\n\n"
        "Введите новые данные в формате:\n"
        "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
        "Пример: <code>Александр / 180 / 75 / 30 / похудение</code>\n\n"
        "Для отмены нажмите /start",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(lambda message: len(message.text.split('/')) == 5)
async def handle_profile_data(message: types.Message):
    try:
        name, height, weight, age, goal = [x.strip() for x in message.text.split('/')]
        
        # Валидация данных
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
            "✅ <b>Данные успешно сохранены!</b>\n"
            "Выберите действие:",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    except ValueError as e:
        await message.answer(
            f"❌ <b>Ошибка:</b> {str(e)}\n\n"
            "Правильный формат:\n"
            "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
            "Пример: <code>Иван / 180 / 75 / 30 / похудение</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения: {str(e)}")
        await message.answer(
            "❌ <b>Произошла ошибка при сохранении</b>",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )

@router.message()
async def handle_other_messages(message: types.Message):
    if await check_user_profile(message.from_user.id):
        await message.answer(
            "Выберите действие:",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "Для начала работы введите данные в формате:\n"
            "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
            "Пример: <code>Александр / 180 / 75 / 30 / похудение</code>",
            parse_mode="HTML"
        )

async def main():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())