from database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer

class UserFollowerModel(Base):
    __tablename__ = "followers"
    id = Column(Integer,primary_key=True)
    user_id = Column(Integer ,ForeignKey("users.id",ondelete="cascade"))
    follower_id = Column(Integer,ForeignKey("users.id",ondelete='cascade'))
    created_at = Column(DateTime,default=datetime.utcnow())

