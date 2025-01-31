from fastapi import HTTPException,APIRouter,Depends
from sqlalchemy.orm import Session
from database import get_db
from src.functionality.comment.comment import create_comment,delete_comment
from src.functionality.comment.commentlike import comment_like
from src.resource.comment.schema import CommentSchema,CommentLikeSchema


comment_router = APIRouter(tags=["Comment"])


@comment_router.post("/create-comment/")
def user_coment(comment:CommentSchema,db:Session=Depends(get_db)):
    try:
       comm = create_comment(comments=comment,db=db)
       return comm
    except Exception as e:
      raise HTTPException(status_code=400,detail=str(e))
    
@comment_router.post("/comment-like/")
def user_comment_like(like:CommentLikeSchema,db:Session=Depends(get_db)):
   try:
      likes= comment_like(like=like,db=db)
      return  likes
   except Exception as e:
      raise HTTPException(status_code=500,detail=str(e))
   
@comment_router.delete("/comment-delete/{comment_id}/")
def user_comment_del(comment_id:int,db:Session=Depends(get_db)):
   try:
      delete = delete_comment(comment_id=comment_id,db=db)
      return delete
   except Exception as e:
      raise HTTPException(status_code=500,detail=str(e))