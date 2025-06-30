import aiohttp
import uuid
from config import GIGACHAT_AUTH_KEY

class GigaChatAPI:
    def __init__(self):
        self.auth_key = GIGACHAT_AUTH_KEY
        self.access_token = None

async def _get_token(self):
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        'Authorization': f'Bearer {self.auth_key}',
        'RqUID': str(uuid.uuid4()),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, verify_ssl=False) as resp:  # <- Здесь
            data = await resp.json()
            self.access_token = data['access_token']
            return self.access_token

async def ask(self, prompt: str):
    token = await self._get_token()
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data, verify_ssl=False) as resp:  # <- И здесь
            return await resp.json()