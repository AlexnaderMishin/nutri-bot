import aiohttp
import uuid
from datetime import datetime, timedelta
from config import GIGACHAT_AUTH_KEY

class GigaChatAPI:
    def __init__(self):
        self.auth_key = GIGACHAT_AUTH_KEY
        self.access_token = None
        self.token_expires = None

    def _get_access_token(self):
        """Получение нового токена доступа (синхронный метод)"""
        if self.access_token and datetime.now() < self.token_expires:
            return self.access_token

        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            'Authorization': f'Bearer {self.auth_key}',
            'RqUID': str(uuid.uuid4()),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            self.access_token = response.json().get('access_token')
            self.token_expires = datetime.now() + timedelta(minutes=25)
            return self.access_token
        raise Exception("Failed to get GigaChat access token")

    async def ask_question(self, question: str) -> str:
        """Асинхронная отправка вопроса в GigaChat и получение ответа"""
        token = self._get_access_token()
        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": question}]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                result = await response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')