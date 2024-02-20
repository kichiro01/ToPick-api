import logging
from fastapi import APIRouter, Depends
from api.db import get_db
from api.schemas import user_schema
from sqlalchemy.ext.asyncio import AsyncSession
from api.cruds import user_cruds

router = APIRouter()
logger = logging.getLogger('uvicorn')

# 新規ユーザー作成
@router.get("/user/create", response_model=user_schema.createUserResponse)
async def createUser(db: AsyncSession = Depends(get_db)):
    return await user_cruds.createUser(db)