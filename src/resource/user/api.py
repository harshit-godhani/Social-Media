from fastapi import HTTPException,APIRouter,Depends, Security,Request
from fastapi.security import HTTPAuthorizationCredentials
from src.resource.user.model import UserModel
from src.functionality.user.user import create_user,user_login,user_reset_pass,user_forgot_pass,user_veritfy_otp,user_delete
from src.resource.user.schema import UserSchema,UserLoginSchema,UserResetPassSchema,UserForgetPassSchema,UserVerifyOtpSchema
from sqlalchemy.orm import Session
from database import get_db
from src.utils.utils import create_access_token, security
from src.config import Config
from jose import jwt  
from datetime import timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(key_func=get_remote_address)


ALO = Config.ALGORITHM
SEC = Config.SECRET_KEY
ACCESS = Config.ACCESS_TOKEN
REFRESH = Config.REFRESH_TOKEN

user_router = APIRouter()

@user_router.post("/register/",tags=["Auth"])
def user_regi(user:UserSchema,db:Session= Depends(get_db)):
    try:
        register = create_user(user=user,db=db)
        return register
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e)) 
    
@user_router.post("/login/",tags=["Auth"])
def user_log(user:UserLoginSchema,db:Session= Depends(get_db)):
    try:
        login = user_login(user=user,db=db)
        return login
    except Exception as e:
        return HTTPException(status_code=500,detail=str(e))
    
@user_router.get("/get-users/",tags=["Auth"])
@limiter.limit("5/second")
def get_all_users(request:Request,db: Session = Depends(get_db)):
    try:
        users = db.query(UserModel).all()
        return {"massage":"API Throttimg aplyed"},users
    except Exception as e:
        return HTTPException(status_code=500,detail=Depends(str(e)))
    
@user_router.post("/forget-password/",tags=["Auth"])
def for_pass(user:UserForgetPassSchema,db:Session=Depends(get_db),token :str = Security(security)):
    try:
        forgetpass = user_forgot_pass(user=user,db=db,token=token)
        return forgetpass
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@user_router.post("/reset-password/",tags=["Auth"])
def rset_password(request:UserResetPassSchema, db:Session = Depends(get_db),token :str = Security(security)):
    try:
        resetpass = user_reset_pass(request=request,db=db,token=token)
        return resetpass
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    
@user_router.post("/verify-otp/",tags=["Auth"])
def vfy_otp(request:UserVerifyOtpSchema,db:Session=Depends(get_db)):
    try:
        verify =user_veritfy_otp(request=request,db=db)

        return verify
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@user_router.delete("/user-delete/{user_id}",tags=["Auth"])
def del_user(user_id:int,db:Session=Depends(get_db),token :str = Security(security)):
    try:
        dels = user_delete(user_id=user_id,db=db,token=token)
        return dels
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    
@user_router.post("/refresh/",tags=["Token"])
def new_access_token(refresh_token:HTTPAuthorizationCredentials=Security(security)):
    token = refresh_token.credentials

    payload = jwt.decode(token,SEC,ALO)

    new_access_token = create_access_token(
        data={"sub":payload["sub"]},
        expires_delta= timedelta(minutes=ACCESS)
    )
    return{"access_token":new_access_token}
