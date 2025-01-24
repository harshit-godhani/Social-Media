from fastapi import HTTPException
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt,JWTError
import smtplib,random

security = HTTPBearer()

SECRET_KEY = "insta-app"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_token(token: str):
    secret_key = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    algorithms = ["HS256"]
    try:
        payload = jwt.decode(token, secret_key, algorithms=algorithms)
        return payload
    except jwtError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    

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
    return str(random.randint(10000,99999))
    
def hash_password(password:str):
    return pwd_context.hash(password)

def verify_password(pain_password,hashed_password): 
    return pwd_context.verify(pain_password,hashed_password)
    

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token:str):
    security_token = "insta-app"
    algorithm = ["HS256"]
    try:
        payload = jwt.decode(token,security_token,algorithms=algorithm)
        return payload
    except JWTError:
        raise HTTPException(status_code=401,detail="Invalid or expire token")
    