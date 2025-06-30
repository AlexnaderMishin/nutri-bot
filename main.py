from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import BOT_TOKEN, FATSECRET_CLIENT_ID, FATSECRET_CLIENT_SECRET
from database import save_user, get_user_data, save_food_entry, get_today_food_entries, get_food_item, add_food_item 
import asyncio
import logging
import datetime
import aiohttp
from requests_oauthlib import OAuth1
import os
from fatsecret_api import (
    search_foods,
    get_food_details,
    parse_nutrition_data,
    search_and_get_nutrition
)
# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
router = Router()

# Состояния для FSM
class FoodEntryStates(StatesGroup):
    waiting_for_food_name = State()
    waiting_for_calories = State()
    waiting_for_protein = State()
    waiting_for_fats = State()
    waiting_for_carbs = State()
    choosing_from_search = State()

# Клавиатуры
def get_commands_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/profile"), KeyboardButton(text="/update")],
            [KeyboardButton(text="/diary"), KeyboardButton(text="/add_food")],
            [KeyboardButton(text="/help")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите команду..."
    )

def get_food_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍎 Яблоко"), KeyboardButton(text="🥩 Курица")],
            [KeyboardButton(text="🍚 Рис"), KeyboardButton(text="🥑 Авокадо")],
            [KeyboardButton(text="🍌 Банан"), KeyboardButton(text="🥚 Яйцо")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True
    )

def get_confirm_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да"), KeyboardButton(text="Нет")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )

# Проверка профиля пользователя
async def check_user_profile(user_id: int) -> bool:
    return get_user_data(user_id) is not None

# ==================== FatSecret API ====================
def get_fatsecret_auth():
    return OAuth1(
        FATSECRET_CLIENT_ID,
        FATSECRET_CLIENT_SECRET,
        signature_type='auth_header'
    )

async def search_foods_fatsecret(query: str):
    url = "https://platform.fatsecret.com/rest/server.api"
    params = {
        "method": "foods.search",
        "search_expression": query,
        "format": "json",
        "max_results": 5
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, auth=get_fatsecret_auth()) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("foods", {}).get("food", [])
    except Exception as e:
        logger.error(f"FatSecret API error: {e}")
    return None

async def get_food_details_fatsecret(food_id: str):
    url = "https://platform.fatsecret.com/rest/server.api"
    params = {
        "method": "food.get",
        "food_id": food_id,
        "format": "json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, auth=get_fatsecret_auth()) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("food", {})
    except Exception as e:
        logger.error(f"FatSecret API error: {e}")
    return None

# ==================== ОСНОВНЫЕ КОМАНДЫ ====================
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        f"👋 <b>Добро пожаловать в FoodTracker!</b>\n\n"
        f"📅 Сегодня: {datetime.datetime.now().strftime('%d.%m.%Y')}\n\n"
    )
    
    if not await check_user_profile(message.from_user.id):
        await message.answer(
            welcome_text +
            "Я помогу вам отслеживать ваше питание и прогресс.\n"
            "Введите данные в формате:\n"
            "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
            "Пример: <code>Александр / 180 / 75 / 30 / похудение</code>",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            welcome_text +
            "Ваш профиль уже заполнен. Используйте команды ниже 👇",
            reply_markup=get_commands_keyboard(),
            parse_mode="HTML"
        )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "ℹ️ <b>Доступные команды:</b>\n\n"
        "/profile - Ваш профиль\n"
        "/update - Обновить данные\n"
        "/diary - Дневник питания\n"
        "/add_food - Добавить прием пищи\n"
        "/help - Справка\n\n"
        "📊 <i>Теперь добавление продуктов стало проще!</i>",
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

# ==================== ДНЕВНИК ПИТАНИЯ ====================
@router.message(Command("diary"))
async def show_diary(message: types.Message):
    entries = get_today_food_entries(message.from_user.id)
    
    if not entries:
        await message.answer(
            "📝 <b>Дневник питания пуст</b>\n"
            "Используйте /add_food чтобы добавить запись",
            parse_mode="HTML"
        )
        return
    
    total = {'calories': 0, 'protein': 0, 'fats': 0, 'carbs': 0}
    text = "📊 <b>Ваш дневник питания</b>\n\n"
    
    for idx, entry in enumerate(entries, 1):
        text += (
            f"{idx}. 🍴 <u>{entry.food_name}</u>\n"
            f"   🔥 {entry.calories} ккал  "
            f"🥩 {entry.protein}г  "
            f"🥑 {entry.fats}г  "
            f"🍞 {entry.carbs}г\n\n"
        )
        
        total['calories'] += entry.calories
        total['protein'] += entry.protein
        total['fats'] += entry.fats
        total['carbs'] += entry.carbs
    
    text += (
        "🧮 <b>Итого за день:</b>\n"
        f"🔥 <i>{total['calories']}</i> ккал\n"
        f"🥩 Белки: <i>{total['protein']:.1f}</i>г\n"
        f"🥑 Жиры: <i>{total['fats']:.1f}</i>г\n"
        f"🍞 Углеводы: <i>{total['carbs']:.1f}</i>г"
    )
    
    await message.answer(text, parse_mode="HTML")

# ==================== ДОБАВЛЕНИЕ ПРОДУКТА ====================
async def confirm_food_data(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Сохраняем в локальную базу для будущего использования
    add_food_item(
        name=data['food_name'],
        calories=data['calories'],
        protein=data['protein'],
        fats=data['fats'],
        carbs=data['carbs']
    )
    
    await message.answer(
        "✅ <b>Продукт успешно добавлен!</b>\n\n"
        f"🍏 {data['food_name']}\n"
        f"🔥 {data['calories']} ккал\n"
        f"🥩 {data['protein']}г белков\n"
        f"🥑 {data['fats']}г жиров\n"
        f"🍞 {data['carbs']}г углеводов",
        parse_mode="HTML",
        reply_markup=get_commands_keyboard()
    )
    await state.clear()

@router.message(Command("add_food"))
async def start_food_entry(message: types.Message, state: FSMContext):
    if not await check_user_profile(message.from_user.id):
        await message.answer("Сначала заполните профиль через /start")
        return
    
    await message.answer(
        "🍎 <b>Введите название продукта:</b>\n"
        "<i>Или выберите из быстрого меню</i>",
        parse_mode="HTML",
        reply_markup=get_food_keyboard()
    )
    await state.set_state(FoodEntryStates.waiting_for_food_name)

@router.message(F.text == "Отмена")
async def cancel_food_entry(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Добавление отменено",
        reply_markup=get_commands_keyboard()
    )

@router.message(FoodEntryStates.waiting_for_food_name)
async def process_food_name(message: types.Message, state: FSMContext):
    # Сначала проверяем локальную базу
    item = get_food_item(message.text)
    if item:
        await state.update_data({
            "food_name": item.name,
            "calories": item.calories,
            "protein": item.protein,
            "fats": item.fats,
            "carbs": item.carbs
        })
        await confirm_food_data(message, state)
        return
    
    # Если нет в локальной базе - ищем в FatSecret
    await message.answer("🔍 Ищу продукт в базе данных...")
    foods = await search_foods_fatsecret(message.text)
    
    if foods:
        if isinstance(foods, list):
            # Показываем список найденных продуктов
            keyboard = []
            for food in foods[:5]:
                name = food.get('food_name', 'Неизвестно')
                food_id = food.get('food_id', '')
                keyboard.append([KeyboardButton(text=f"{name} ({food_id})")])
            
            await message.answer(
                "Выберите продукт:",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=keyboard,
                    resize_keyboard=True
                )
            )
            await state.set_state(FoodEntryStates.choosing_from_search)
        else:
            # Найден один продукт
            await process_fatsecret_food(message, state, foods)
    else:
        await message.answer(
            "Продукт не найден. Введите данные вручную:\n"
            "🔥 <b>Калорийность (на 100г):</b>\n"
            "<i>Пример: 52</i>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(FoodEntryStates.waiting_for_calories)

async def process_fatsecret_food(message: types.Message, state: FSMContext, food_data):
    food_id = food_data.get('food_id')
    if not food_id:
        await message.answer("Ошибка: не найден ID продукта")
        return
    
    details = await get_food_details_fatsecret(food_id)
    if not details:
        await message.answer("Не удалось получить детали продукта")
        return
    
    servings = details.get('servings', {}).get('serving', [])
    if not servings:
        await message.answer("Нет информации о пищевой ценности")
        return
    
    # Берем первую порцию (обычно 100г)
    serving = servings[0] if isinstance(servings, list) else servings
    
    await state.update_data({
        "food_name": details.get('food_name', 'Неизвестно'),
        "calories": float(serving.get('calories', 0)),
        "protein": float(serving.get('protein', 0)),
        "fats": float(serving.get('fat', 0)),
        "carbs": float(serving.get('carbohydrate', 0))
    })
    await confirm_food_data(message, state)

@router.message(FoodEntryStates.choosing_from_search)
async def handle_food_choice(message: types.Message, state: FSMContext):
    if "(" in message.text and ")" in message.text:
        food_id = message.text.split("(")[-1].rstrip(")")
        food_data = {"food_id": food_id}
        await process_fatsecret_food(message, state, food_data)
    else:
        await message.answer("Неверный формат. Попробуйте еще раз.")

@router.message(FoodEntryStates.waiting_for_calories)
async def process_calories(message: types.Message, state: FSMContext):
    try:
        calories = float(message.text)
        await state.update_data(calories=calories)
        await message.answer(
            "🥩 <b>Белки (г на 100г):</b>\n"
            "<i>Пример: 0.3</i>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(FoodEntryStates.waiting_for_protein)
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(FoodEntryStates.waiting_for_protein)
async def process_protein(message: types.Message, state: FSMContext):
    try:
        protein = float(message.text)
        await state.update_data(protein=protein)
        await message.answer(
            "🥑 <b>Жиры (г на 100г):</b>\n"
            "<i>Пример: 0.2</i>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(FoodEntryStates.waiting_for_fats)
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(FoodEntryStates.waiting_for_fats)
async def process_fats(message: types.Message, state: FSMContext):
    try:
        fats = float(message.text)
        await state.update_data(fats=fats)
        await message.answer(
            "🍞 <b>Углеводы (г на 100г):</b>\n"
            "<i>Пример: 14</i>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(FoodEntryStates.waiting_for_carbs)
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(FoodEntryStates.waiting_for_carbs)
async def process_carbs(message: types.Message, state: FSMContext):
    try:
        carbs = float(message.text)
        data = await state.get_data()
        
        save_food_entry(
            user_id=message.from_user.id,
            food_name=data['food_name'],
            calories=data['calories'],
            protein=data['protein'],
            fats=data['fats'],
            carbs=carbs
        )
        
        await message.answer(
            "✅ <b>Продукт успешно добавлен!</b>\n\n"
            f"🍏 {data['food_name']}\n"
            f"🔥 {data['calories']} ккал\n"
            f"🥩 {data['protein']}г белков\n"
            f"🥑 {data['fats']}г жиров\n"
            f"🍞 {carbs}г углеводов",
            parse_mode="HTML",
            reply_markup=get_commands_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

# ==================== ОБНОВЛЕНИЕ ПРОФИЛЯ ====================
@router.message(Command("update"))
async def update_profile(message: types.Message):
    await message.answer(
        "✏️ Введите новые данные в формате:\n"
        "<b>Имя / Рост / Вес / Возраст / Цель</b>\n\n"
        "Пример: <code>Александр / 180 / 75 / 30 / похудение</code>",
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
            parse_mode="HTML"
        )

# ==================== ЗАПУСК БОТА ====================
async def main():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())