import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.models import user_model

def setCreateDate(model):
    now = datetime.datetime.now()
    model.created_at = now
    model.updated_at = now
    return

async def checkIfUserExist(db: AsyncSession, user_id: int):
    userInDb = await db.get(user_model.User, user_id)
    if not userInDb:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found")
    return