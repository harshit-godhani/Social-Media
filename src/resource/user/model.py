from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from database import Base


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    follower_count = Column(Integer,default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
