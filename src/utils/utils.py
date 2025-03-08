from fastapi import HTTPException
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt,JWTError
import smtplib,random
from src.config import Config

security = HTTPBearer()

secret_key =Config.SECRET_KEY
algorithm = Config.ALGORITHM
access_token = Config.ACCESS_TOKEN
refresh_token = Config.REFRESH_TOKEN

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def send_email(to_email, subject, body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "godhaniharshit871@gmail.com"
    sender_password = "qjld nqxz zqps bknw"
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(sender_email, to_email, message)
    except Exception as e:
        raise Exception(f"Error sending email: {str(e)}")
    
def otp_genrates():
    return str(random.randint(1000,9999))
    
def hash_password(password:str):
    return pwd_context.hash(password)

def verify_password(pain_password,hashed_password): 
    return pwd_context.verify(pain_password,hashed_password)
    

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=access_token))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=refresh_token))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)

def verify_token(token:str):
    security_token = "insta-app"
    algorithm = ["HS256"]
    try:
        payload = jwt.decode(token,security_token,algorithms=algorithm)
        return payload
    except JWTError:
        raise HTTPException(status_code=401,detail="Invalid or expire token")
    