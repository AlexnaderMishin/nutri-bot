import aiohttp
import uuid
from config import GIGACHAT_AUTH_KEY
from gigachat import GigaChat
from config import GIGACHAT_TOKEN

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
            async with session.post(url, headers=headers) as resp:
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
            async with session.post(url, headers=headers, json=data) as resp:
                return await resp.json()
            
def get_nutrition_plan(weight, height, age, goal):
    prompt = f"Рассчитай КБЖУ для {weight}кг, рост {height}см, возраст {age}, цель: {goal}."
    giga = GigaChat(credentials=GIGACHAT_TOKEN, verify_ssl_certs=False)
    response = giga.chat(prompt)
    return response.choices[0].message.content