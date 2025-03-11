from datetime import datetime
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from  src.resource.post.schema import PostLikeSchema
from src.resource.post.model import PostModel,PostLikeModel
from src.resource.user.model import UserModel
from database import get_db



def post_like(like: PostLikeSchema, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == like.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if like.post_id:

        post = db.query(PostModel).filter(PostModel.id == like.post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        
    db_post_like = PostLikeModel(
        post_id=like.post_id,
        user_id=like.user_id,
        created_at=datetime.utcnow()
    )
    db.add(db_post_like)
    db.commit()
    db.refresh(db_post_like)
    return {"Status":"Success",
            "message": "Like created successfully",
        "data":{
            "like_id": db_post_like.id,
            "user_id":db_post_like.user_id,
            "post_id": db_post_like.post_id,
            "created_at":db_post_like.created_at
        }
            }