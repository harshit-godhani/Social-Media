from fastapi import HTTPException
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt,JWTError
import smtplib,random,os
from src.config import Config

security = HTTPBearer()

secret_key =Config.SECRET_KEY
algorithm = Config.ALGORITHM
access_token = Config.ACCESS_TOKEN
refresh_token = Config.REFRESH_TOKEN

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def send_email(to_email, subject, body):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = os.getenv("SMTP_EMAIL")
    SENDER_PASSWORD = os.getenv("SMTP_PASSWORD")
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(SENDER_EMAIL, to_email, message)
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
    