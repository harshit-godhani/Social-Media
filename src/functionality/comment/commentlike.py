from datetime import datetime
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from  src.resource.comment.schema import CommentLikeSchema
from src.resource.comment.model import CommentModel,CommentLikeModel
from src.resource.post.model import PostModel
from src.resource.user.model import UserModel
from database import get_db




def comment_like(like: CommentLikeSchema, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == like.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if like.post_id:

        post = db.query(PostModel).filter(PostModel.id == like.post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
    if like.comment_id:
        comment = db.query(CommentModel).filter(CommentModel.id == like.comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
    db_comment_like = CommentLikeModel(
        post_id=like.post_id,
        comment_id=like.comment_id,
        user_id=like.user_id,
        created_at=datetime.utcnow()
    )
    db.add(db_comment_like)
    db.commit()
    db.refresh(db_comment_like)
    return {"Status":"Success",
            "message": "Like created successfully",
        "data":{
            "like_id": db_comment_like.id,
            "user_id":db_comment_like.user_id,
            "comment_id" : db_comment_like.comment_id,
            "post_id": db_comment_like.post_id,
            "created_at":db_comment_like.created_at
        }
            }