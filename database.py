from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    height = Column(Integer)
    weight = Column(Integer)
    age = Column(Integer)
    goal = Column(String)

engine = create_engine('sqlite:///nutri.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def save_user(user_id, name, height, weight, age, goal):
    session = Session()
    user = User(id=user_id, name=name, height=height, weight=weight, age=age, goal=goal)
    session.add(user)
    session.commit()