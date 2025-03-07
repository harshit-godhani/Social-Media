from sqlalchemy import Column, ForeignKey, Integer,Text,DateTime
from database import Base
from datetime import datetime
from sqlalchemy.orm import relationship


class CommentModel(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    user = relationship('UserModel')
    user_id = Column(Integer, ForeignKey('users.id',ondelete="cascade"), nullable=False)
    post = relationship('PostModel')
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    created_at = Column(DateTime,default=datetime.utcnow())

class CommentLikeModel(Base):
    __tablename__ = "commentlikes"
    id = Column(Integer, primary_key=True, index=True)
    user = relationship('UserModel')
    user_id = Column(Integer, ForeignKey('users.id',ondelete="cascade"), nullable=False)
    post = relationship('PostModel')
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    comment = relationship('CommentModel')
    comment_id = Column(Integer, ForeignKey('comments.id'), nullable=False)
    created_at = Column(DateTime,default=datetime.utcnow())