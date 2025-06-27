import aiohttp
import uuid
import ssl
from datetime import datetime, timedelta
from config import GIGACHAT_AUTH_KEY
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GigaChatAPI:
    def __init__(self):
        self.auth_key = GIGACHAT_AUTH_KEY
        self.access_token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        self.ssl_context = self._create_ssl_context()

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Создает кастомный SSL-контекст для Railway"""
        context = ssl.create_default_context()
        # Добавляем доверенные корневые сертификаты
        context.load_default_certs()
        # Дополнительные настройки для обхода проблем с сертификатами
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # Внимание! Для продакшена нужно настроить правильно
        return context

    async def _get_token(self) -> str:
        """Получает новый токен доступа с обработкой SSL-ошибок"""
        try:
            if self.access_token and datetime.now() < self.token_expires:
                return self.access_token

            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            headers = {
                'Authorization': f'Bearer {self.auth_key}',
                'RqUID': str(uuid.uuid4()),
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            connector = aiohttp.TCPConnector(
                ssl_context=self.ssl_context,
                limit=1,
                force_close=True
            )

            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                trust_env=True
            ) as session:
                async with session.post(url, headers=headers) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"HTTP {resp.status}: {error_text}")
                    
                    data = await resp.json()
                    self.access_token = data['access_token']
                    self.token_expires = datetime.now() + timedelta(minutes=25)
                    return self.access_token

        except Exception as e:
            logger.error(f"Token request failed: {str(e)}")
            raise Exception(f"Не удалось получить токен: {str(e)}")

    async def ask(self, prompt: str) -> dict:
        """Отправляет запрос к GigaChat API с повторной попыткой при ошибке"""
        max_retries = 2
        for attempt in range(max_retries):
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
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    trust_env=True
                ) as session:
                    async with session.post(url, headers=headers, json=data) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            raise Exception(f"HTTP {resp.status}: {error_text}")
                        
                        return await resp.json()

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"GigaChat request failed after {max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")

async def get_nutrition_plan(weight: float, height: float, age: int, goal: str) -> str:
    """Генерирует персонализированный план питания"""
    try:
        prompt = (
            f"Создай детальный план питания для:\n"
            f"- Вес: {weight} кг\n"
            f"- Рост: {height} см\n"
            f"- Возраст: {age} лет\n"
            f"- Цель: {goal}\n\n"
            "Включи:\n"
            "1. Суточную калорийность\n"
            "2. Распределение БЖУ\n"
            "3. 3 варианта меню\n"
            "4. Рекомендации по времени приема пищи"
        )
        
        giga = GigaChatAPI()
        response = await giga.ask(prompt)
        return response['choices'][0]['message']['content']
        
    except Exception as e:
        logger.error(f"Nutrition plan generation failed: {str(e)}")
        return f"⚠️ Ошибка генерации плана: {str(e)}"
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