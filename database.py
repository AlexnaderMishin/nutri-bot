from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, timedelta
from config import DATABASE_URL
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
    user_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    goal = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FoodEntry(Base):
    __tablename__ = 'food_entries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    food_name = Column(String(100), nullable=False)
    calories = Column(Integer, nullable=False)
    protein = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    portion_size = Column(Float, default=100.0)  # Размер порции в граммах

class FoodItem(Base):
    __tablename__ = 'food_items'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    calories = Column(Integer, nullable=False)
    protein = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Настройки подключения для PostgreSQL на Railway
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Важно для поддержания соединения
    pool_recycle=3600,   # Пересоздавать соединения каждый час
    connect_args={
        'connect_timeout': 10,
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 5
    }
)

# Сессия с автоматическим управлением
Session = scoped_session(
    sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False
    )
)

def get_session():
    return Session()

def safe_create_tables():
    """Создает таблицы, если они не существуют"""
    with engine.connect() as conn:
        # Получаем список всех таблиц в БД
        existing_tables = set(
            row[0] for row in conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ).fetchall()
        )
        
        # Создаем только отсутствующие таблицы
        for table_class in [User, FoodEntry, FoodItem]:
            if table_class.__tablename__ not in existing_tables:
                table_class.__table__.create(conn)
                logger.info(f"Создана таблица {table_class.__tablename__}")

# Функции для работы с пользователями
def save_user(user_id: int, name: str, height: float, weight: float, age: int, goal: str) -> bool:
    """Сохраняет или обновляет данные пользователя"""
    if not check_db_connection():
        logger.error("Нет подключения к БД")
        return False

    session = get_session()
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
        
        # Проверяем, что данные действительно сохранились
        saved_user = session.query(User).filter(User.user_id == user_id).first()
        if not saved_user:
            raise Exception("Пользователь не был сохранен")
            
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка сохранения пользователя {user_id}: {str(e)}")
        return False
    finally:
        Session.remove()

def get_user_data(user_id: int) -> Optional[Dict]:
    """Возвращает данные пользователя в виде словаря"""
    session = get_session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
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
        logger.error(f"Ошибка получения данных пользователя: {e}")
        return None
    finally:
        Session.remove()

#проверка соединения с бд
def check_db_connection():
    """Проверяет соединение с базой данных"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return False
    
# Функции для работы с дневником питания
def save_food_entry(
    user_id: int,
    food_name: str,
    calories: int,
    protein: float,
    fats: float,
    carbs: float,
    portion_size: float = 100.0
) -> bool:
    """Сохраняет запись о приеме пищи"""
    session = get_session()
    try:
        session.add(FoodEntry(
            user_id=user_id,
            food_name=food_name,
            calories=calories,
            protein=protein,
            fats=fats,
            carbs=carbs,
            portion_size=portion_size
        ))
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка сохранения записи о питании: {e}")
        return False
    finally:
        Session.remove()

def get_today_food_entries(user_id: int) -> List[Dict]:
    """Возвращает записи о питании за сегодня"""
    session = get_session()
    try:
        today = datetime.utcnow().date()
        entries = session.query(FoodEntry).filter(
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
        logger.error(f"Ошибка получения записей о питании: {e}")
        return []
    finally:
        Session.remove()

# Функции для работы с кэшем продуктов
def get_food_item(name: str) -> Optional[Dict]:
    """Ищет продукт в локальной базе по названию"""
    session = get_session()
    try:
        item = session.query(FoodItem).filter(
            func.lower(FoodItem.name) == func.lower(name)
        ).first()
        
        return {
            "name": item.name,
            "calories": item.calories,
            "protein": item.protein,
            "fats": item.fats,
            "carbs": item.carbs
        } if item else None
    except Exception as e:
        logger.error(f"Ошибка поиска продукта: {e}")
        return None
    finally:
        Session.remove()

def add_food_item(name: str, calories: int, protein: float, fats: float, carbs: float) -> bool:
    """Добавляет продукт в локальную базу"""
    session = get_session()
    try:
        session.add(FoodItem(
            name=name.lower(),
            calories=calories,
            protein=protein,
            fats=fats,
            carbs=carbs
        ))
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка добавления продукта: {e}")
        return False
    finally:
        Session.remove()

def search_food_items(query: str, limit: int = 5) -> List[Dict]:
    """Ищет продукты по названию"""
    session = get_session()
    try:
        items = session.query(FoodItem).filter(
            FoodItem.name.ilike(f"%{query}%")
        ).limit(limit).all()
        
        return [{
            "name": item.name,
            "calories": item.calories,
            "protein": item.protein,
            "fats": item.fats,
            "carbs": item.carbs
        } for item in items]
    except Exception as e:
        logger.error(f"Ошибка поиска продуктов: {e}")
        return []
    finally:
        Session.remove()

# Инициализация БД при первом запуске
try:
    safe_create_tables()
    logger.info("Проверка таблиц БД завершена")
except Exception as e:
    logger.error(f"Ошибка инициализации БД: {e}")

if __name__ == "__main__":
    print("=== Тест подключения к БД ===")
    try:
        safe_create_tables()
        print("Таблицы успешно созданы/проверены")
        
        with get_session() as session:
            print("\nСтруктура таблиц:")
            for table in [User, FoodEntry, FoodItem]:
                print(f"- {table.__tablename__}: {[c.name for c in table.__table__.columns]}")
            
            print("\nСтатистика:")
            print(f"Пользователей: {session.query(User).count()}")
            print(f"Записей о питании: {session.query(FoodEntry).count()}")
            print(f"Продуктов в базе: {session.query(FoodItem).count()}")
    except Exception as e:
        print(f"Ошибка: {e}")