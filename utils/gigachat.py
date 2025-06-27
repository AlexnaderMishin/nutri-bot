import aiohttp
import uuid
import ssl
import certifi
from datetime import datetime, timedelta
from config import GIGACHAT_AUTH_KEY
import logging

logger = logging.getLogger(__name__)

class GigaChatAPI:
    def __init__(self):
        self.auth_key = GIGACHAT_AUTH_KEY
        self.access_token = None
        self.token_expires = None
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    async def _get_token(self):
        try:
            # Проверяем, есть ли действующий токен
            if self.access_token and datetime.now() < self.token_expires:
                return self.access_token

            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            headers = {
                'Authorization': f'Bearer {self.auth_key}',
                'RqUID': str(uuid.uuid4()),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Настраиваем безопасное подключение
            connector = aiohttp.TCPConnector(
                ssl_context=self.ssl_context,
                limit=10,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.post(url, headers=headers) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    self.access_token = data['access_token']
                    self.token_expires = datetime.now() + timedelta(minutes=25)
                    logger.info("GigaChat token получен успешно")
                    return self.access_token
                    
        except Exception as e:
            logger.error(f"Ошибка получения токена GigaChat: {str(e)}")
            raise Exception(f"Не удалось получить токен: {str(e)}")

    async def ask(self, prompt: str):
        try:
            token = await self._get_token()
            url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            data = {
                "model": "GigaChat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            connector = aiohttp.TCPConnector(ssl_context=self.ssl_context)
            timeout = aiohttp.ClientTimeout(total=15)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    resp.raise_for_status()
                    response = await resp.json()
                    logger.debug(f"GigaChat response: {response}")
                    return response
                    
        except Exception as e:
            logger.error(f"Ошибка запроса к GigaChat: {str(e)}")
            raise Exception(f"Ошибка API GigaChat: {str(e)}")

async def get_nutrition_plan(weight, height, age, goal):
    try:
        prompt = (
            f"Создай детальный план питания со следующими параметрами:\n"
            f"- Вес: {weight} кг\n"
            f"- Рост: {height} см\n"
            f"- Возраст: {age} лет\n"
            f"- Цель: {goal}\n\n"
            "Включи:\n"
            "1. Рекомендуемую калорийность\n"
            "2. Баланс БЖУ\n"
            "3. Пример меню на день\n"
            "4. Рекомендации по питанию"
        )
        
        giga = GigaChatAPI()
        response = await giga.ask(prompt)
        return response['choices'][0]['message']['content']
        
    except Exception as e:
        logger.error(f"Ошибка генерации плана питания: {str(e)}")
        return f"⚠️ Не удалось сгенерировать план питания. Ошибка: {str(e)}"
# import aiohttp
# import uuid
# from config import GIGACHAT_AUTH_KEY
# from gigachat import GigaChat
# from config import GIGACHAT_TOKEN

# class GigaChatAPI:
#     def __init__(self):
#         self.auth_key = GIGACHAT_AUTH_KEY
#         self.access_token = None

#     async def _get_token(self):
#         url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
#         headers = {
#             'Authorization': f'Bearer {self.auth_key}',
#             'RqUID': str(uuid.uuid4()),
#             'Content-Type': 'application/x-www-form-urlencoded'
#         }
        
#         async with aiohttp.ClientSession() as session:
#             async with session.post(url, headers=headers) as resp:
#                 data = await resp.json()
#                 self.access_token = data['access_token']
#                 return self.access_token

#     async def ask(self, prompt: str):
#         token = await self._get_token()
#         url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
#         headers = {
#             'Authorization': f'Bearer {token}',
#             'Content-Type': 'application/json'
#         }
#         data = {
#             "model": "GigaChat",
#             "messages": [{"role": "user", "content": prompt}],
#             "temperature": 0.7
#         }
        
#         async with aiohttp.ClientSession() as session:
#             async with session.post(url, headers=headers, json=data) as resp:
#                 return await resp.json()
            
# def get_nutrition_plan(weight, height, age, goal):
#     prompt = f"Рассчитай КБЖУ для {weight}кг, рост {height}см, возраст {age}, цель: {goal}."
#     giga = GigaChat(credentials=GIGACHAT_TOKEN, verify_ssl_certs=False)
#     response = giga.chat(prompt)
#     return response.choices[0].message.content