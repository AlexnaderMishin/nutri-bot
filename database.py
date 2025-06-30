from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL
import logging

# Настройка логирования SQL
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, index=True)
    name = Column(String(100))
    height = Column(Float)
    weight = Column(Float)
    age = Column(Integer)
    goal = Column(String(100))
    # Убрали created_at для совместимости с существующей БД

class FoodEntry(Base):
    __tablename__ = 'food_entries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    food_name = Column(String(100))
    calories = Column(Integer)
    protein = Column(Float)
    fats = Column(Float)
    carbs = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)

# Настройка подключения для Railway
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

Session = sessionmaker(bind=engine)

def init_db():
    """Инициализация базы данных с проверкой структуры"""
    inspector = inspect(engine)
    
    # Создаем таблицу food_entries, если ее нет
    if 'food_entries' not in inspector.get_table_names():
        FoodEntry.__table__.create(engine)
    
    # Проверяем основные таблицы
    Base.metadata.create_all(engine)

# Функции для работы с пользователями
def save_user(user_id: int, name: str, height: float, weight: float, age: int, goal: str):
    session = Session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.name = name
            user.height = height
            user.weight = weight
            user.age = age
            user.goal = goal
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

# Функции для работы с питанием
def save_food_entry(user_id: int, food_name: str, calories: int, protein: float, fats: float, carbs: float):
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
    session = Session()
    try:
        today = datetime.utcnow().date()
        return session.query(FoodEntry).filter(
            FoodEntry.user_id == user_id,
            func.date(FoodEntry.date) == today
        ).all()
    finally:
        session.close()

# Инициализация при импорте
init_db()