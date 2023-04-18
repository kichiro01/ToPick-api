from fastapi import FastAPI
from api.routers import auth, mylist, brows

app = FastAPI()
app.include_router(mylist.router)
app.include_router(auth.router)
app.include_router(brows.router)
