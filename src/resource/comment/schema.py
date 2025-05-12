from pydantic import BaseModel
from datetime import datetime

class CommentSchema(BaseModel):
    user_id : int
    post_id : int
    text : str


class CommentLikeSchema(BaseModel):
    user_id : int
    post_id : int
    comment_id : int
    