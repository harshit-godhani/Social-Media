from pydantic import BaseModel
from datetime import datetime

class PostSchema(BaseModel):
    title : str
    content : str
    user_id : int

class PostLikeSchema(BaseModel):
    user_id : int
    post_id : int

class PostUpdateSchema(BaseModel):
    id : int
    title : str
    content : str

class PostLikeSchema(BaseModel):
    user_id : int
    post_id : int
    