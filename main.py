import os
import requests
import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class GigaChatAPI:
    def __init__(self):
        self.token = None
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self._auth()

    def _auth(self):
        """Аутентификация в API GigaChat"""
        try:
            url = f"{self.base_url}/oauth"
            payload = {
                'scope': 'GIGACHAT_API_PERS'
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': os.getenv('GIGA_RQUID'),
                'Authorization': f"Basic {os.getenv('GIGA_AUTH_TOKEN')}"
            }
            
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            self.token = response.json()['access_token']
            
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            raise Exception("Ошибка аутентификации в GigaChat")

    async def ask(self, user_prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """Отправка запроса к GigaChat API"""
        try:
            if not self.token:
                self._auth()

            url = f"{self.base_url}/chat/completions"
            
            messages = []
            
            # Системный промпт из скриншота
            if not system_prompt:
                system_prompt = """
                # Профессиональный AI-бот нутрициолог
                
                Ты - опытный помощник в области здорового питания и диетологии. 
                Составляешь персонализированные планы питания с точным расчетом КБЖУ.
                
                Требования:
                - Только научно обоснованные рекомендации
                - Учет индивидуальных параметров
                - Четкие граммовки и калорийность
                - Профессиональный тон без излишней фамильярности
                """
            
            messages.append({
                "role": "system",
                "content": system_prompt.strip()
            })
            
            messages.append({
                "role": "user",
                "content": user_prompt
            })
            
            payload = {
                "model": "GigaChat-2-Max",
                "messages": messages,
                "temperature": 0.7,
                "profanity_check": True,
                "max_tokens": 2000
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f"Bearer {self.token}"
            }
            
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            raise Exception("Ошибка при запросе к GigaChat API")