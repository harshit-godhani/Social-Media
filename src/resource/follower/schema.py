from pydantic import BaseModel


class FollowerSchema(BaseModel):
    user_id : int
    follower_id : int

class UnfollowSchema(BaseModel):
    user_id : int
    follower_id : int

class AllfollowerSchema(BaseModel):
    user_id : int
    