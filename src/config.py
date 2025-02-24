import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_TOKEN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    REFRESH_TOKEN = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))
    DB_URL = os.getenv("DATABASE_URL")

