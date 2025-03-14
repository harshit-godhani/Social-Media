from datetime import datetime
from fastapi.security import HTTPBearer
from src.resource.user.model import UserModel
from src.resource.user.schema import UserSchema,UserResetPassSchema,UserForgetPassSchema,UserLoginSchema,UserVerifyOtpSchema
from sqlalchemy.orm import Session
from src.utils.utils import create_access_token,create_refresh_token,pwd_context,verify_password,otp_genrates,send_email,verify_token
from fastapi import HTTPException,Depends, Security
from database import get_db
from pydantic import validate_email


security = HTTPBearer()

otp_store={}

def create_user(user:UserSchema,db : Session = Depends (get_db)):
    try:
        validate_email(user.email)
    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))


    db_user =db.query(UserModel).filter(UserModel.email==user.email).first()
    if db_user:
        raise HTTPException(status_code=200,detail="Email already register")
    
    hash_password = pwd_context.hash(user.password)

    db_user= UserModel(username=user.username,
                       email=user.email,
                       password=hash_password,
                       created_at=datetime.utcnow()
                    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    otp = otp_genrates()
    otp_store[user.email] = otp
    

    subejct = "This is Test mail server form Roy..!"
    body=f"Your OTP code is {otp} ...It will expire in 1 minutes."
    
    try:
        send_email(to_email=user.email,subject=subejct,body=body)
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Faild to send OTP email: {str(e)}")
    return {
        "status":True,
        "User_id":db_user.id,   
        "Email":"Your OTP send successfully --> Check your email",
        "Messgae":"Please OTP verified !!",
        "Created_at":db_user.created_at
        }

def user_login(user:UserLoginSchema,db : Session =Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email==user.email).first()

    if  not db_user or not verify_password(user.password,db_user.password):
        raise HTTPException(status_code=400,detail="Incorrect deatlis...!")

    access_token = create_access_token(data={"id":db_user.id})
    refresh_token = create_refresh_token(data={})

    return {
        "status":True,
        "Message":"Login Successfully",
        "user_id":db_user.id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

  
def user_forgot_pass(user:UserForgetPassSchema,db:Session=Depends(get_db),token :str = Security(security)):
    db_user = db.query(UserModel).filter(UserModel.email==user.email).first()
    try:
      token_data = verify_token(token.credentials)
    except Exception :
        raise HTTPException(status_code=400,detail="Invalid or expire token")

    if not db_user:
        raise HTTPException(status_code=404,detail="User email not found ")

    otp = otp_genrates()
    otp_store[user.email]=otp
   
    body = "Reset passowrd "
    subejct = f"OTP is deliverd on email Pelase verify {otp}...It will expire in 1 minutes"

    try:
        send_email(to_email=user.email,subject=subejct,body=body)
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Faild to send OTP email: {str(e)}")
    
    return {
        "Status":True,
        "Message":"OTP has been sent on Your E-Mail..."
        }


def user_veritfy_otp(request:UserVerifyOtpSchema):
    if request.email not in otp_store:
        raise HTTPException(status_code=404,detail="OTP is not valid Its Expires")

    
    stored_otp = otp_store[request.email]

    if request.otp != stored_otp:
        raise HTTPException(status_code=400,detail="Inavlid OTP please try again...!!!")
    
    del otp_store[request.email]

    return{
        "Status":True,
        "message":"OTP veryfied successfully",
        "user":"User Successfully Register"
        }


def user_reset_pass(request :UserResetPassSchema,db:Session = Depends(get_db),token :str = Security(security)):
    db_user =db.query(UserModel).filter(UserModel.username == request.username).first()
    try:
      token_data = verify_token(token.credentials)
    except Exception :
        raise HTTPException(status_code=400,detail="Invalid or expire token")

    if not db_user:
        raise HTTPException(status_code=404,detail="User not found and name is mismathced")
    
    if request.new_password != request.conform_password:
        raise HTTPException(status_code=400,detail="New password and conform passwprd does not matched")
    
    hash_password = pwd_context.hash(request.new_password)
       
    db_user.password = hash_password
    db.commit()

    return{
        "Status":True,
        "Message":"Password reset successfully"
    }


def user_delete(user_id:int,db:Session=Depends(get_db),token :str = Security(security)):
    try:
      token_data = verify_token(token.credentials)
    except Exception :
        raise HTTPException(status_code=400,detail="Invalid or expire token")
      
    user  = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
          raise HTTPException(status_code=404,detail="User not found")
      
    db.delete(user)
    db.commit()
      
    return{
        "Status":True,
        "Message":"User deleted successfully",
        "user_id":user_id
        }