import logging
from fastapi import APIRouter, Depends
from api.db import get_db
from api.schemas import user as userSchema
from sqlalchemy.ext.asyncio import AsyncSession
import api.cruds.user as user_crud

router = APIRouter()
logger = logging.getLogger('uvicorn')

# 新規ユーザー作成
@router.get("/user/create", response_model=userSchema.createUserResponse)
async def createUser(db: AsyncSession = Depends(get_db)):
    return await user_crud.createUser(db)