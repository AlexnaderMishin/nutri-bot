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