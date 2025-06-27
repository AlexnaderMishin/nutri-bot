import aiohttp
import uuid
import ssl
from datetime import datetime, timedelta
from config import GIGACHAT_AUTH_KEY
import logging
from typing import Optional
import json

logger = logging.getLogger(__name__)

class GigaChatAPI:
    def __init__(self):
        self.auth_key = GIGACHAT_AUTH_KEY
        self.access_token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        self.ssl_context = self._create_ssl_context()

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Создаем SSL контекст с правильными настройками"""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # Только для тестирования!
        return context

    async def _get_token(self) -> str:
        """Получаем токен с правильным форматом запроса"""
        try:
            if self.access_token and datetime.now() < self.token_expires:
                return self.access_token

            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            
            # Правильные заголовки и данные для GigaChat API
            headers = {
                'Authorization': f'Bearer {self.auth_key}',
                'RqUID': str(uuid.uuid4()),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Важно: scope должен быть в теле запроса
            data = {
                'scope': 'GIGACHAT_API_PERS'
            }

            connector = aiohttp.TCPConnector(
                ssl_context=self.ssl_context,
                limit=1
            )

            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.post(
                    url,
                    headers=headers,
                    data=data  # Важно: отправляем как form-data
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Token error: {error_text}")
                        raise Exception(f"HTTP {resp.status}: {error_text}")
                    
                    response_data = await resp.json()
                    self.access_token = response_data.get('access_token')
                    if not self.access_token:
                        raise Exception("No access token in response")
                    
                    self.token_expires = datetime.now() + timedelta(minutes=25)
                    return self.access_token

        except Exception as e:
            logger.error(f"Token request failed: {str(e)}")
            raise Exception(f"Не удалось получить токен: {str(e)}")

    async def ask(self, prompt: str) -> dict:
        """Отправляем запрос к API с обработкой ошибок"""
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

            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl_context=self.ssl_context),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=data
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"HTTP {resp.status}: {error_text}")
                    
                    return await resp.json()

        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise Exception(f"Ошибка API GigaChat: {str(e)}")
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