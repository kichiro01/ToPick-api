from fastapi import FastAPI
from api.routers import auth, mylist

app = FastAPI()
app.include_router(mylist.router)
app.include_router(auth.router)
