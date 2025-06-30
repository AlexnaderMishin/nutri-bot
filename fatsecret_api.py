import aiohttp
from requests_oauthlib import OAuth1
from config import FATSECRET_CLIENT_ID, FATSECRET_CLIENT_SECRET
import logging
from typing import Optional, Dict, List, Union

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://platform.fatsecret.com/rest/server.api"

def get_fatsecret_auth():
    """Возвращает объект аутентификации OAuth1 для FatSecret API"""
    return OAuth1(
        FATSECRET_CLIENT_ID,
        FATSECRET_CLIENT_SECRET,
        signature_type='auth_header'
    )

async def search_foods(query: str, max_results: int = 5) -> Optional[List[Dict]]:
    """
    Поиск продуктов по названию
    Возвращает список продуктов или None при ошибке
    """
    params = {
        "method": "foods.search",
        "search_expression": query,
        "format": "json",
        "max_results": max_results
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                BASE_URL,
                params=params,
                auth=get_fatsecret_auth()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    foods = data.get("foods", {}).get("food", [])
                    return foods if isinstance(foods, list) else [foods]
                logger.error(f"API error: {response.status}")
    except Exception as e:
        logger.error(f"Search foods error: {str(e)}")
    return None

async def get_food_details(food_id: str) -> Optional[Dict]:
    """
    Получение детальной информации о продукте по ID
    Возвращает словарь с данными или None при ошибке
    """
    params = {
        "method": "food.get",
        "food_id": food_id,
        "format": "json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                BASE_URL,
                params=params,
                auth=get_fatsecret_auth()
            ) as response:
                if response.status == 200:
                    return await response.json()
                logger.error(f"API error: {response.status}")
    except Exception as e:
        logger.error(f"Get food details error: {str(e)}")
    return None

async def parse_nutrition_data(food_data: Dict) -> Optional[Dict[str, Union[str, float]]]:
    """
    Парсинг данных о пищевой ценности из ответа API
    Возвращает словарь с нормализованными данными
    """
    try:
        if not food_data:
            return None
            
        food = food_data.get("food", {})
        servings = food.get("servings", {}).get("serving", [])
        
        if not servings:
            return None
            
        # Берем первую порцию (обычно 100г)
        serving = servings[0] if isinstance(servings, list) else servings
        
        return {
            "name": food.get("food_name", "Неизвестно"),
            "calories": float(serving.get("calories", 0)),
            "protein": float(serving.get("protein", 0)),
            "fats": float(serving.get("fat", 0)),
            "carbs": float(serving.get("carbohydrate", 0))
        }
    except Exception as e:
        logger.error(f"Parse nutrition error: {str(e)}")
        return None

async def search_and_get_nutrition(query: str) -> Optional[Dict[str, Union[str, float]]]:
    """
    Комбинированная функция: поиск + получение данных о первом найденном продукте
    """
    foods = await search_foods(query)
    if not foods:
        return None
        
    first_food = foods[0] if isinstance(foods, list) else foods
    food_id = first_food.get("food_id")
    if not food_id:
        return None
        
    food_details = await get_food_details(food_id)
    return await parse_nutrition_data(food_details)