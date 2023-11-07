from fastapi import FastAPI
from api.routers import discover, auth, mylist, browse, user

app = FastAPI()
app.include_router(browse.router)
app.include_router(mylist.router)
app.include_router(auth.router)
app.include_router(discover.router)
app.include_router(user.router)
