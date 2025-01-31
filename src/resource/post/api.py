from fastapi import APIRouter, Depends, File, Form, HTTPException, Security, UploadFile
from src.resource.post.schema import PostLikeSchema, PostSchema,PostUpdateSchema
from sqlalchemy.orm import Session
from database import get_db
from src.functionality.post.post import create_post,post_update,read_all_post,delete_post
from src.functionality.post.postlike import post_like
from src.utils.utils import security


post_router = APIRouter(tags=["User-Post"])

@post_router.post("/create-post/")
def create_user_post(user_id: int = Form(...),
                     title: str = Form(...),
                     content: str = Form(...),
                     db: Session = Depends(get_db),
                     image: UploadFile = File(...)
                    ):
    try:
        user_post = PostSchema(title=title,content=content, user_id=user_id)
        post = create_post(post=user_post,db=db,image=image)
        return post
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@post_router.patch("/update-post/")
def user_post_update(post:PostUpdateSchema,db:Session=Depends(get_db)):
    try:
        patch_post=post_update(post=post,db=db)
        return patch_post
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@post_router.get("/post-read-all/")
def get_post(db:Session=Depends(get_db)):
    try:

        posts=read_all_post(db=db)
        return posts
    except Exception:
        raise HTTPException(status_code=404,detail="Not found")


@post_router.delete("/post-delete/{post_id}/",)
def del_post(post_id:int,db:Session=Depends(get_db),token :str = Security(security)):
    try:
        dels = delete_post(post_id=post_id,db=db)
        return dels
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    
@post_router.post("/post-like/")
def likedis_coment(like:PostLikeSchema,db:Session=Depends(get_db)):
   try:
      likedis= post_like(like=like,db=db)
      return  likedis
   except Exception as e:
      raise HTTPException(status_code=500,detail=str(e))