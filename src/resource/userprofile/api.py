from fastapi import APIRouter,HTTPException,Depends,Security
from database import get_db
from src.resource.userprofile.schema import UserProfileViewSchema,UserProfileUpdateschema
from sqlalchemy.orm import Session
from src.functionality.userprofile.userprofileview import profile_view_user,profile_update_user
from fastapi.security import HTTPBearer

security = HTTPBearer()

profile_router = APIRouter()

@profile_router.get("/profile-view/")
def view_user_profile(profile:UserProfileViewSchema,db:Session=Depends(get_db)):
    try:
        response = profile_view_user(profile.username,db=db)
        return response
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    
@profile_router.put("/profile-edit/")
def edit_profile(update:UserProfileUpdateschema,db:Session=Depends(get_db),token: str = Security(security)):
    try:
        response = profile_update_user(update=update,db=db,token=token)
        return response
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))