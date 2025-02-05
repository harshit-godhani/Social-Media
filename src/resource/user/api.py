from fastapi import HTTPException,APIRouter,Depends, Security
from src.resource.user.model import UserModel
from src.functionality.user.user import create_user,user_login,user_reset_pass,user_forgot_pass,user_veritfy_otp,user_delete
from src.resource.user.schema import UserSchema,UserLoginSchema,UserResetPassSchema,UserForgetPassSchema,UserVerifyOtpSchema
from sqlalchemy.orm import Session
from database import get_db
from src.utils.utils import security

user_router = APIRouter(tags=["Auth"])

@user_router.post("/register/")
def user_regi(user:UserSchema,db:Session= Depends(get_db)):
    try:
        register = create_user(user=user,db=db)
        return register
    except Exception as e:
        return HTTPException(status_code=500,detail=str(e)) 
    
@user_router.post("/login/")
def user_log(user:UserLoginSchema,db:Session= Depends(get_db)):
    try:
        login = user_login(user=user,db=db)
        return login
    except Exception as e:
        return HTTPException(status_code=500,detail=str(e))
    
@user_router.get("/users/")
def get_all_users(db: Session = Depends(get_db)):
    try:
        users = db.query(UserModel).all()
        return users
    except Exception as e:
        return HTTPException(status_code=500,detail=Depends(str(e)))
    
@user_router.post("/forget-password/")
def for_pass(user:UserForgetPassSchema,db:Session=Depends(get_db)):
    try:
        forgetpass = user_forgot_pass(user=user,db=db)
        return forgetpass
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@user_router.post("/reset-password/")
def rset_password(request:UserResetPassSchema, db:Session = Depends(get_db)):
    try:
        resetpass = user_reset_pass(request=request,db=db)
        return resetpass
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    
@user_router.post("/verify-otp/")
def vfy_otp(request:UserVerifyOtpSchema,db:Session=Depends(get_db)):
    try:
        verify =user_veritfy_otp(request=request,db=db)

        return verify
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@user_router.delete("/user-delete/{user_id}")
def del_user(user_id:int,db:Session=Depends(get_db),token :str = Security(security)):
    try:
        dels = user_delete(user_id=user_id,db=db,token=token)
        return dels
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
