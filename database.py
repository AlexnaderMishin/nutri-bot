from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL
import logging

# Отключаем логирование SQLAlchemy в продакшене
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

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
    date = Column(DateTime, default=datetime.utcnow)

# Упрощенное подключение для Railway
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=300
)

# Проверяем и создаем таблицы безопасно
def safe_create_tables():
    with engine.connect() as conn:
        # Проверяем существование таблиц через raw SQL
        users_exists = conn.execute(
            "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'users')"
        ).scalar()
        
        food_entries_exists = conn.execute(
            "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'food_entries')"
        ).scalar()

        if not users_exists:
            User.__table__.create(conn)
        if not food_entries_exists:
            FoodEntry.__table__.create(conn)

# Создаем сессию с отключенным автофлушем
Session = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)

def get_session():
    return Session()

# Функции для работы с пользователями
def save_user(user_id: int, name: str, height: float, weight: float, age: int, goal: str):
    session = get_session()
    try:
        existing = session.query(User).filter(User.user_id == user_id).first()
        if existing:
            existing.name = name
            existing.height = height
            existing.weight = weight
            existing.age = age
            existing.goal = goal
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

def get_user_data(user_id: int):
    session = get_session()
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
    session = get_session()
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
    session = get_session()
    try:
        today = datetime.utcnow().date()
        return session.query(FoodEntry).filter(
            FoodEntry.user_id == user_id,
            func.date(FoodEntry.date) == today
        ).all()
    finally:
        session.close()

# Инициализация при первом запуске
try:
    safe_create_tables()
except Exception as e:
    print(f"Ошибка инициализации БД: {e}")
    
if __name__ == "__main__":
    print("Проверка подключения к БД...")
    try:
        safe_create_tables()
        print("Таблицы успешно созданы/проверены")
        print("Структура users:", [c.name for c in User.__table__.columns])
        print("Структура food_entries:", [c.name for c in FoodEntry.__table__.columns])
    except Exception as e:
        print(f"Ошибка: {e}")