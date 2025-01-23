from database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from src.resource.comment.model import CommentModel
from src.resource.comment.schema  import CommentSchema

def create_comment(comments:CommentSchema,db:Session=Depends(get_db)):

    db_comments = CommentModel(
        user_id= comments.user_id,
        post_id= comments.post_id,
        text = comments.text
    )
    db.add(db_comments)
    db.commit()
    db.refresh(db_comments)


    return{
        "Status":"Success",
        "Message":"Comment Created Successfully",
        "id":db_comments.id,
        "user_id":db_comments.user_id,
        "post_id":db_comments.post_id,
        "created_at":db_comments.created_at
        
    }

def delete_comment(comment_id:CommentSchema,db:Session=Depends(get_db)):

    db_comment = db.query(CommentModel).filter(CommentModel.id==comment_id).first()

    if not db_comment:
        raise HTTPException(status_code=404,detail="Comment not found")
    
    db.delete(db_comment)
    db.commit()
    return{
        "Staus":"Success",
        "Message":"Comment deleted successfully",
        "Deleted_Comment_id":comment_id
    }