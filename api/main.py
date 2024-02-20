from fastapi import FastAPI
from api.routers import admin_router, auth_router, browse_router, contact_router, discover_router, mylist_router, user

app = FastAPI()
app.include_router(browse_router.router)
app.include_router(mylist_router.router)
app.include_router(auth_router.router)
app.include_router(discover_router.router)
app.include_router(user.router)
app.include_router(contact_router.router)
app.include_router(admin_router.router)
