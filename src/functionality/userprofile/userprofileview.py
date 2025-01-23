from fastapi import HTTPException,Depends,Security
from src.resource.userprofile.schema import UserProfileViewSchema,UserProfileUpdateschema
from sqlalchemy.orm import Session
from database import get_db
from src.resource.user.model import UserModel
from src.utils.utils import hash_password,verify_token
from fastapi.security import HTTPBearer

security = HTTPBearer()

def profile_view_user(username: UserProfileViewSchema, db: Session = Depends(get_db)):
    user_data = db.query(UserModel).filter(UserModel.username == username).first()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True,
            "user": {
                "username": user_data.username,
                "email": user_data.email,
                "created_at": user_data.created_at,
            }
        }
    
def profile_update_user(update: UserProfileUpdateschema, db: Depends = Session(get_db), token: str = Security(security)):
    try:
        current_user = verify_token(token.credentials)
    except HTTPException:
        raise HTTPException(status_code=400, detail="Invalid or expired token. Please log in again.")
    
    if not update.user_id:
        raise HTTPException(status_code=400, detail="Missing 'user_id' in request.")

    # if current_user["id"] != update.user_id:
    #     raise HTTPException(status_code=400, detail="User ID mismatch.")
    
    user = db.query(UserModel).filter(UserModel.id == update.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {update.user_id} not found.")
    
    if update.username:
        user.username = update.username
    if update.password:
        user.password = hash_password(update.password)
    if update.email:
        user.email = update.email
    
    db.commit()

    return {
        "success": True,
        "message": "Profile edited successfully."
    }
