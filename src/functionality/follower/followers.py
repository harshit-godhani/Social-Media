from fastapi import HTTPException,Depends
from sqlalchemy.orm import Session
from src.resource.user.model import UserModel
from src.resource.follower.model import UserFollowerModel
from src.resource.follower.schema import FollowerSchema,UnfollowSchema,AllfollowerSchema
from database import get_db
from datetime import datetime


def user_follower(follower:FollowerSchema,db:Session=Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == follower.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    follow_data = db.query(UserModel).filter(UserModel.id == follower.follower_id).first()
    if not follow_data:
        raise HTTPException(status_code=404,detail="follower not found!")
    
    db_follower=UserFollowerModel(
        user_id=follower.user_id,
        follower_id=follower.follower_id,
        created_at=datetime.utcnow()
    )
    user.follower_count = (user.follower_count or 0) +1

    db.add(db_follower)
    db.commit()
    db.refresh(db_follower)

    return {
        "success":True,
        "message":f"you successfully followed user whoses user_id is {follower.follower_id}.",
        "created_at":db_follower.created_at
    }

def user_unfollower(unfollow_user:UnfollowSchema,db:Session=Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == unfollow_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    unfollow_data = db.query(UserFollowerModel).filter(UserFollowerModel.follower_id == unfollow_user.follower_id).first()
    if not unfollow_data:
        raise HTTPException(status_code=404,detail="follower not found!")
        
    db.delete(unfollow_data)
    db.commit()

    user.follower_count = (user.follower_count or 0) -1
    db.commit()

    return {"success":True,
            "message":f"you successfully unfollowed user whoses user_id is {unfollow_user.user_id}."
        }

def get_all_follower(fetch_follower:AllfollowerSchema,db:Session=Depends(get_db)):
        user = db.query(UserModel).filter(UserModel.id == fetch_follower.user_id).first()
        return {
            "success":True,
            "message":"All Followers of this user..",
            "Follower_count":user.follower_count
        }