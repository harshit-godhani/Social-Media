from pydantic import BaseModel
from datetime import datetime

class UserSchema(BaseModel):
    username : str
    email : str
    password : str

class UserLoginSchema(BaseModel):
    email: str
    password: str

class UserForgetPassSchema(BaseModel):
    email :str

class UserResetPassSchema(BaseModel):
    username : str
    new_password:str
    conform_password:str  

class UserVerifyOtpSchema(BaseModel):
    email:str
    otp:str 

