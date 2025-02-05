from pydantic import BaseModel,EmailStr


class UserSchema(BaseModel):
    username : str
    email : EmailStr
    password : str

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class UserForgetPassSchema(BaseModel):
    email : EmailStr

class UserResetPassSchema(BaseModel):
    username : str
    new_password:str
    conform_password:str  

class UserVerifyOtpSchema(BaseModel):
    email: EmailStr
    otp: int

