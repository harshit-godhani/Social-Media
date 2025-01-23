from fastapi import APIRouter,HTTPException,Depends
from sqlalchemy.orm import Session
from src.resource.follower.schema import FollowerSchema,UnfollowSchema,AllfollowerSchema
from database import get_db
from src.functionality.follower.followers import user_follower,user_unfollower,get_all_follower

follower_router = APIRouter()


@follower_router.post("/user-follow/")
def follow_user(follower:FollowerSchema,db:Session=Depends(get_db)):
    try:
        response = user_follower(follower=follower,db=db)
        return response
    except Exception as e:
        raise HTTPException(status_code=404,detail=str(e))

@follower_router.delete("/user-unfollow/")
def unfollow_user_id(unfollow_user:UnfollowSchema,db:Session=Depends(get_db)):
    try:
        response = user_unfollower(unfollow_user=unfollow_user,db=db)
        return response
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    
@follower_router.get("/follower-count/")
def fetch_all_follower(fetch_follower:AllfollowerSchema,db:Session=Depends(get_db)):
    try:
        response = get_all_follower(fetch_follower=fetch_follower,db=db)
        return response
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))