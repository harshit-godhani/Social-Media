from pydantic import BaseModel

class UserProfileViewSchema(BaseModel):
    username: str

class UserProfileUpdateschema(BaseModel):
    user_id : int
    email : str
    username : str
    password : str