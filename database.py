from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL
import os

# Инициализация базы данных с улучшенными настройками для Railway
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600    # Переподключение каждые 60 минут
)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, index=True)  # Добавлен индекс для ускорения поиска
    name = Column(String(100))
    height = Column(Float)
    weight = Column(Float)
    age = Column(Integer)
    goal = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)  # UTC время для Railway

class FoodEntry(Base):
    __tablename__ = 'food_entries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)  # Индекс для частых запросов
    food_name = Column(String(100))
    calories = Column(Integer)
    protein = Column(Float)
    fats = Column(Float)
    carbs = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)  # Используем UTC для консистентности

    # Для PostgreSQL на Railway добавляем композитный индекс
    __table_args__ = (
        {'postgresql_using': 'btree'} if 'postgresql' in DATABASE_URL else {}
    )

# Создаем таблицы
Base.metadata.create_all(bind=engine)

# Настройка сессии с учетом особенностей Railway
Session = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)

def save_user(user_id: int, name: str, height: float, weight: float, age: int, goal: str):
    """Оптимизированная функция сохранения пользователя"""
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
            session.add(User(
                user_id=user_id,
                name=name,
                height=height,
                weight=weight,
                age=age,
                goal=goal
            ))
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_user_data(user_id: int) -> dict:
    """Оптимизированный запрос данных пользователя"""
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
    except Exception as e:
        raise e
    finally:
        session.close()

def save_food_entry(user_id: int, food_name: str, calories: int, protein: float, fats: float, carbs: float):
    """Безопасное добавление записи о питании"""
    session = Session()
    try:
        session.add(FoodEntry(
            user_id=user_id,
            food_name=food_name,
            calories=calories,
            protein=protein,
            fats=fats,
            carbs=carbs
        ))
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_today_food_entries(user_id: int):
    """Оптимизированный запрос записей за сегодня"""
    session = Session()
    try:
        today = datetime.utcnow().date()  # Используем UTC для Railway
        return session.query(FoodEntry).filter(
            FoodEntry.user_id == user_id,
            func.date(FoodEntry.created_at) == today
        ).order_by(FoodEntry.created_at.desc()).all()  # Сортировка по дате
    finally:
        session.close()