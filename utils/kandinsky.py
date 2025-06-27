import requests
from config import KANDINSKY_TOKEN

def generate_meal_image(prompt):
    url = "https://api.kandinsky.ai/generate"
    headers = {"Authorization": f"Bearer {KANDINSKY_TOKEN}"}
    data = {"prompt": prompt, "width": 512, "height": 512}
    response = requests.post(url, headers=headers, json=data)
    return response.json()["url"]