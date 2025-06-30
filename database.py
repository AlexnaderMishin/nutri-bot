from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import DATABASE_URL
import logging
import os

# Проверка наличия DATABASE_URL
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан. Проверьте настройки в Railway")

# Настройка логирования SQL-запросов
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

class FoodEntry(Base):
    __tablename__ = 'food_entries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    food_name = Column(String(100))
    calories = Column(Integer)
    protein = Column(Float)
    fats = Column(Float)
    carbs = Column(Float)
    created_at = Column(DateTime, server_default=func.now())  # Используем серверное время

# Настройка подключения для PostgreSQL на Railway
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=300,    # Переподключение каждые 5 минут
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

# Автоматическое создание таблиц при первом подключении
def init_db():
    try:
        with engine.connect() as conn:
            # Проверяем существование таблиц
            users_exist = conn.execute(
                "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'users')"
            ).scalar()
            
            if not users_exist:
                Base.metadata.create_all(engine)
                print("Таблицы успешно созданы")
            else:
                print("Таблицы уже существуют")
    except Exception as e:
        print(f"Ошибка при инициализации БД: {e}")
        raise

init_db()

# Настройка сессии
Session = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)

def get_db():
    """Генератор сессий для FastAPI или других фреймворков"""
    db = Session()
    try:
        yield db
    finally:
        db.close()

# Пример использования (можно удалить в продакшене)
if __name__ == "__main__":
    print("Проверка подключения к PostgreSQL на Railway...")
    try:
        with Session() as session:
            count = session.execute("SELECT COUNT(*) FROM pg_tables").scalar()
            print(f"В базе есть {count} таблиц(а)")
            print("Подключение успешно!")
    except Exception as e:
        print(f"Ошибка подключения: {e}")