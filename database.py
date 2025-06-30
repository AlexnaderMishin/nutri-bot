from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime  # Добавляем импорт
from config import DATABASE_URL
import os

# Инициализация базы данных
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    name = Column(String(100))
    height = Column(Float)
    weight = Column(Float)
    age = Column(Integer)
    goal = Column(String(100))

class FoodEntry(Base):
    __tablename__ = 'food_entries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    food_name = Column(String(100))
    calories = Column(Integer)
    protein = Column(Float)
    fats = Column(Float)
    carbs = Column(Float)
    date = Column(DateTime, default=datetime.now)  # Исправлено: datetime.now без скобок

# Создаем таблицы
Base.metadata.create_all(bind=engine)

# Фабрика сессий
Session = sessionmaker(bind=engine)

def save_user(user_id: int, name: str, height: float, weight: float, age: int, goal: str):
    session = Session()
    try:
        existing_user = session.query(User).filter(User.user_id == user_id).first()
        if existing_user:
            existing_user.name = name
            existing_user.height = height
            existing_user.weight = weight
            existing_user.age = age
            existing_user.goal = goal
        else:
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
    session = Session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        return {
            "name": user.name,
            "height": user.height,
            "weight": user.weight,
            "age": user.age,
            "goal": user.goal
        } if user else None
    finally:
        session.close()

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
    session = Session()
    try:
        today = datetime.now().date()
        return session.query(FoodEntry).filter(
            FoodEntry.user_id == user_id,
            func.date(FoodEntry.date) == today
        ).all()
    finally:
        session.close()