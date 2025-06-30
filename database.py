from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
import logging

# Настройка логирования
logging.basicConfig()
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

# Подключение с таймаутами для Railway
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    connect_args={
        "connect_timeout": 5,
        "keepalives": 1,
        "keepalives_idle": 30
    }
)

# Создаем таблицы при старте
def init_db():
    with engine.connect() as conn:
        # Проверяем существование таблиц
        users_exist = conn.execute(
            text("SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'users')")
        ).scalar()
        
        if not users_exist:
            conn.execute(text("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE,
                    name VARCHAR(100),
                    height FLOAT,
                    weight FLOAT,
                    age INTEGER,
                    goal VARCHAR(100)
                )
            """))
        
        food_entries_exist = conn.execute(
            text("SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'food_entries')")
        ).scalar()
        
        if not food_entries_exist:
            conn.execute(text("""
                CREATE TABLE food_entries (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    food_name VARCHAR(100),
                    calories INTEGER,
                    protein FLOAT,
                    fats FLOAT,
                    carbs FLOAT,
                    date TIMESTAMP
                )
            """))
        conn.commit()

# Инициализация
init_db()

# Фабрика сессий
Session = sessionmaker(bind=engine)

def get_db():
    return Session()