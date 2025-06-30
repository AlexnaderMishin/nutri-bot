from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
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

def get_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
            [InlineKeyboardButton(text="✏️ Обновить данные", callback_data="update")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
        ]
    )

def get_commands_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/start"), KeyboardButton(text="/help")],
            [KeyboardButton(text="/profile"), KeyboardButton(text="/update")],
            [KeyboardButton(text="Показать команды")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите команду..."
    )

async def check_user_profile(user_id: int) -> bool:
    return get_user_data(user_id) is not None

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    # Приветственное сообщение
    welcome_text = (
        f"👋 <b>Добро пожаловать в FitnessBot!</b>\n\n"
        f"📅 Сегодня: {datetime.datetime.now().strftime('%d.%m.%Y')}\n\n"
    )
    
    if not await check_user_profile(message.from_user.id):
        full_text = (
            welcome_text +
            "Я помогу вам отслеживать ваши параметры и прогресс.\n"
            "Для начала введите свои данные в формате:\n"
            "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
            "Пример: <code>Александр / 180 / 75 / 30 / похудение</code>"
        )
    else:
        user_data = get_user_data(message.from_user.id)
        full_text = (
            welcome_text +
            f"👤 Ваше имя: {user_data['name']}\n"
            "Выберите действие:"
        )
    
    await message.answer(
        full_text,
        reply_markup=get_commands_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("help") | F.text == "Показать команды")
async def cmd_help(message: types.Message):
    await message.answer(
        "ℹ️ <b>Доступные команды:</b> ℹ️\n\n"
        "/start - Начать работу с ботом\n"
        "/profile - Показать ваш профиль\n"
        "/update - Обновить данные профиля\n"
        "/help - Показать это сообщение\n\n"
        "Или используйте кнопки ниже 👇",
        reply_markup=get_commands_keyboard(),
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

# Добавьте остальные обработчики (profile, update, handle_profile_data) из предыдущего кода
# ...

async def main():
    try:
        dp = Dispatcher()
        dp.include_router(router)
        
        logger.info("Бот успешно запущен!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())