from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
import os

# Инициализация базы данных
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)  # ID пользователя в Telegram
    name = Column(String(100))             # Ограничение длины для PostgreSQL
    height = Column(Float)                 # Рост в см
    weight = Column(Float)                 # Вес в кг
    age = Column(Integer)                  # Возраст
    goal = Column(String(100))             # Цель (похудение, набор массы и т.д.)

# Создаем таблицы (автоматически при первом запуске)
Base.metadata.create_all(bind=engine)

# Создаем фабрику сессий
Session = sessionmaker(bind=engine)

def save_user(user_id: int, name: str, height: float, weight: float, age: int, goal: str):
    """Сохраняет данные пользователя в базу данных"""
    session = Session()
    try:
        # Проверяем, существует ли уже пользователь
        existing_user = session.query(User).filter(User.user_id == user_id).first()
        
        if existing_user:
            # Обновляем существующего пользователя
            existing_user.name = name
            existing_user.height = height
            existing_user.weight = weight
            existing_user.age = age
            existing_user.goal = goal
        else:
            # Создаем нового пользователя
            user = User(
                user_id=user_id,
                name=name,
                height=height,
                weight=weight,
                age=age,
                goal=goal
            )
            session.add(user)
        
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_user_data(user_id: int) -> dict:
    """Получает данные пользователя из базы данных"""
    session = Session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            return {
                "name": user.name,
                "height": user.height,
                "weight": user.weight,
                "age": user.age,
                "goal": user.goal
            }
        return None
    except Exception as e:
        raise e
    finally:
        session.close()

def delete_user(user_id: int) -> bool:
    """Удаляет пользователя из базы данных"""
    session = Session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            session.delete(user)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# В database.py добавляем:
class FoodEntry(Base):
    __tablename__ = 'food_entries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    food_name = Column(String(100))
    calories = Column(Integer)
    protein = Column(Float)  # Б
    fats = Column(Float)     # Ж
    carbs = Column(Float)    # У
    date = Column(DateTime, default=datetime.now())

def save_food_entry(user_id: int, food_name: str, calories: int, protein: float, fats: float, carbs: float):
    session = Session()
    try:
        entry = FoodEntry(
            user_id=user_id,
            food_name=food_name,
            calories=calories,
            protein=protein,
            fats=fats,
            carbs=carbs
        )
        session.add(entry)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_today_food_entries(user_id: int):
    today = datetime.now().date()
    session = Session()
    try:
        return session.query(FoodEntry).filter(
            FoodEntry.user_id == user_id,
            func.date(FoodEntry.date) == today
        ).all()
    finally:
        session.close()