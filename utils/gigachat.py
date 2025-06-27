from gigachat import GigaChat
from config import GIGACHAT_TOKEN

def get_nutrition_plan(weight, height, age, goal):
    prompt = f"Рассчитай КБЖУ для {weight}кг, рост {height}см, возраст {age}, цель: {goal}."
    giga = GigaChat(credentials=GIGACHAT_TOKEN, verify_ssl_certs=False)
    response = giga.chat(prompt)
    return response.choices[0].message.content