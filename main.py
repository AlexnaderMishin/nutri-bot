from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from utils.giga_api import GigaChatAPI
from config import config
import logging

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
giga = GigaChatAPI()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Я бот-нутрициолог. Используй /nutrition для получения плана питания")

@dp.message(Command("nutrition"))
async def send_nutrition(message: types.Message):
    try:
        # Пример пользовательских данных (замените на реальные из БД)
        user_data = {
            'weight': 80,
            'height': 173,
            'age': 25,
            'goal': "Набор массы"
        }
        
        prompt = f"""
        Составь план питания для:
        - Вес: {user_data['weight']} кг
        - Рост: {user_data['height']} см
        - Возраст: {user_data['age']} лет
        - Цель: {user_data['goal']}
        """
        
        response = await giga.ask(prompt)
        plan = response['choices'][0]['message']['content']
        
        await message.answer(plan)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())