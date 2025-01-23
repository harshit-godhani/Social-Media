from datetime import  datetime
import shutil,os
from src.resource.post.model import PostModel
from src.resource.post.schema import PostSchema,PostUpdateSchema
from sqlalchemy.orm import Session
from database import get_db
from fastapi import File, HTTPException,Depends,Security,UploadFile
from src.utils.utils import verify_token,security


def  create_post(post:PostSchema,db: Session=Depends(get_db), image: UploadFile=File(...)):
    try:
        
        upload_folder = "images/"
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, image.filename)

        with open(file_path, "wb") as file_buffer:
            shutil.copyfileobj(image.file, file_buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


    db_post=PostModel(
            user_id= post.user_id,
            title =post.title,
            content=post.content,
            image_url=image.filename,
            created_at=datetime.utcnow(),
        )

    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return{"Status":"Success",
            "message": "Post created successfully",
        "data":{
            "Post_id": db_post.id,
            "title": db_post.title,
            "content" : db_post.content,
            "user_id":db_post.user_id,
            "image_URL" : db_post.image_url
        }
    }
        
def post_update(post:PostUpdateSchema,db:Session=Depends(get_db)):
    db_post= db.query(PostModel).filter(PostModel.id==post.id).first()

    if not db_post:
        raise HTTPException(status_code=404,detail="Post not found")

    db_post.title =post.title
    db_post.content = post.content


    db.commit()
    db.refresh(db_post)
        
    return{
        "Status":"Success",
        "Message":"Post updated successfully",
        "Post_id":db_post.id,
        "Updated_title":db_post.title,
        "Updated_caption":db_post.content,
        "Updated_at":db_post.updated_at
}

def read_all_post(db:Session=Depends(get_db)):
    posts = db.query(PostModel).all()
    if not posts:
        raise HTTPException(status_code=404,detail="No posts found")

    return{
    "Status":"Success",
    "Message":"Posts found successfully",
    "Data":[
        {
            "post_id":post.id,
            "title":post.title,
            "content":post.content,
            "created_at":post.created_at
            } for post in posts
    
    ]
} 

def delete_post(post_id :PostModel,db:Session=Depends(get_db),token :str = Security(security)):
    try:
      token_data = verify_token(token.credentials)
    except Exception :
        raise HTTPException(status_code=400,detail="Invalid or expire token")

    db_post= db.query(PostModel).filter(PostModel.id==post_id).first()
    if not db_post:
        raise HTTPException(status_code=404,detail="Post not found")
    
    db.delete(db_post)
    db.commit()
    return{
        "Status":"Success",
        "Message":"Post deleted successfully",
        "Deleted_post_id":post_id
    }

   