import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import logging
from typing import Optional, Dict, List

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    goal = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class FoodEntry(Base):
    __tablename__ = 'food_entries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    food_name = Column(String(100), nullable=False)
    calories = Column(Integer, nullable=False)
    protein = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    date = Column(DateTime, server_default=func.now(), index=True)
    portion_size = Column(Float, default=100.0)

# Функция для корректировки URL базы данных
def prepare_database_url(db_url: str) -> str:
    if db_url.startswith('postgres://'):
        return db_url.replace('postgres://', 'postgresql://', 1)
    return db_url

# Получаем и корректируем URL базы данных
DATABASE_URL = prepare_database_url(os.getenv('DATABASE_URL', ''))

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Настройка подключения к PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=True,  # Включить для отладки SQL-запросов
    connect_args={
        'connect_timeout': 10,
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 5
    }
)

SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

def get_db():
    """Генератор сессий для зависимостей"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Инициализация базы данных"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# Основные функции работы с данными
def save_user(db, user_id: int, name: str, height: float, weight: float, age: int, goal: str) -> bool:
    """Сохраняет или обновляет данные пользователя"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if user:
            user.name = name
            user.height = height
            user.weight = weight
            user.age = age
            user.goal = goal
        else:
            new_user = User(
                user_id=user_id,
                name=name,
                height=height,
                weight=weight,
                age=age,
                goal=goal
            )
            db.add(new_user)
        
        db.commit()
        
        # Двойная проверка сохранения
        saved_user = db.query(User).filter(User.user_id == user_id).first()
        if not saved_user:
            logger.error("User data was not saved properly")
            return False
            
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving user {user_id}: {str(e)}")
        return False

def get_user_data(db, user_id: int) -> Optional[Dict]:
    """Получает данные пользователя"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            return {
                "name": user.name,
                "height": user.height,
                "weight": user.weight,
                "age": user.age,
                "goal": user.goal,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        return None

def save_food_entry(
    db,
    user_id: int,
    food_name: str,
    calories: int,
    protein: float,
    fats: float,
    carbs: float,
    portion_size: float = 100.0
) -> bool:
    """Сохраняет запись о питании"""
    try:
        entry = FoodEntry(
            user_id=user_id,
            food_name=food_name,
            calories=calories,
            protein=protein,
            fats=fats,
            carbs=carbs,
            portion_size=portion_size
        )
        db.add(entry)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving food entry: {str(e)}")
        return False

def get_today_food_entries(db, user_id: int) -> List[Dict]:
    """Получает записи о питании за сегодня"""
    try:
        today = datetime.utcnow().date()
        entries = db.query(FoodEntry).filter(
            FoodEntry.user_id == user_id,
            func.date(FoodEntry.date) == today
        ).all()
        
        return [{
            "id": entry.id,
            "food_name": entry.food_name,
            "calories": entry.calories,
            "protein": entry.protein,
            "fats": entry.fats,
            "carbs": entry.carbs,
            "portion_size": entry.portion_size,
            "date": entry.date
        } for entry in entries]
    except Exception as e:
        logger.error(f"Error getting food entries: {str(e)}")
        return []

# Инициализация базы данных при импорте
try:
    init_db()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

if __name__ == "__main__":
    # Тестирование подключения
    from sqlalchemy.orm import Session
    
    print("Testing database connection...")
    try:
        db = SessionLocal()
        
        # Проверка существования таблиц
        print("\nExisting tables:")
        tables = db.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """).fetchall()
        for table in tables:
            print(f"- {table[0]}")
        
        # Тестовые данные
        test_user_id = 12345
        if save_user(db, test_user_id, "Test User", 180.0, 75.0, 30, "test"):
            print("\nUser saved successfully")
            user_data = get_user_data(db, test_user_id)
            print("User data:", user_data)
        else:
            print("\nFailed to save user")
        
        db.close()
    except Exception as e:
        print(f"Database test failed: {e}")