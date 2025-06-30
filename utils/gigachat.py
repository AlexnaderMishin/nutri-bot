import requests
import json
from typing import Dict, Any
import logging
from config import GIGACHAT_AUTH_KEY

logger = logging.getLogger(__name__)

class GigaChatAPI:
    def __init__(self):
        self.token = None
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self._auth()

    def _auth(self):
        """Аутентификация в API GigaChat"""
        try:
            response = requests.post(
                f"{self.base_url}/oauth",
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json',
                    'RqUID': "unique-request-id-123",  # Можно генерировать случайный
                    'Authorization': f"Basic {GIGACHAT_AUTH_KEY}"
                },
                data={'scope': 'GIGACHAT_API_PERS'},
                timeout=10
            )
            response.raise_for_status()
            self.token = response.json().get('access_token')
            if not self.token:
                raise Exception("Не получили токен доступа")
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            raise Exception("Ошибка аутентификации в GigaChat")

    async def ask(self, prompt: str) -> Dict[str, Any]:
        """Отправка запроса к GigaChat API"""
        try:
            if not self.token:
                self._auth()

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': f"Bearer {self.token}"
                },
                json={
                    "model": "GigaChat-2-Max",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            raise Exception("Ошибка запроса к GigaChat API")