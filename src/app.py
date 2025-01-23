from fastapi import FastAPI
from database import Base, engine
from src.resource.user.api import user_router
from src.resource.post.api import post_router
from src.resource.comment.api import comment_router
from src.resource.follower.api import follower_router
from src.resource.userprofile.api import profile_router

Base.metadata.create_all(bind=engine) 


app = FastAPI()

app.include_router(user_router)
app.include_router(post_router)
app.include_router(comment_router)
app.include_router(follower_router)
app.include_router(profile_router)

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}
