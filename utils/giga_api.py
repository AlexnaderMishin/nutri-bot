import requests
import json
from typing import Dict, Any
import logging
from config import config

logger = logging.getLogger(__name__)

class GigaChatAPI:
    def __init__(self):
        self.token = None
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self._auth()

    def _auth(self):
        try:
            response = requests.post(
                f"{self.base_url}/oauth",
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json',
                    'RqUID': "UNIQUE_REQUEST_ID",
                    'Authorization': f"Basic {config.GIGACHAT_AUTH_KEY}"
                },
                data={'scope': 'GIGACHAT_API_PERS'},
                timeout=10
            )
            self.token = response.json()['access_token']
        except Exception as e:
            logger.error(f"Auth error: {e}")
            raise Exception("Ошибка аутентификации")

    async def ask(self, prompt: str) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": "GigaChat-2-Max",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            headers = {
                'Authorization': f"Bearer {self.token}",
                'Content-Type': 'application/json'
            }
            response = requests.post(url, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            logger.error(f"API error: {e}")
            raise Exception("Ошибка запроса к API")