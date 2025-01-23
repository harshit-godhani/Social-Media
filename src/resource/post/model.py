from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base


class PostModel(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('UserModel')
    published = Column(DateTime,default=None)
    created_at = Column(DateTime,default=datetime.utcnow())
    updated_at = Column(DateTime,default=datetime.utcnow())
    image_url = Column(String)

class PostLikeModel(Base):
    __tablename__ = "postlikes"
    id = Column(Integer,primary_key=True,index=True)
    user = relationship('UserModel')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post = relationship('PostModel')
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    created_at = Column(DateTime,default=datetime.utcnow())