import logging
from fastapi import APIRouter, Depends
from api.db import get_db
from api.schemas import auth_schema
from sqlalchemy.ext.asyncio import AsyncSession
from api.cruds import auth_cruds
from api.cruds import common_cruds

router = APIRouter()
logger = logging.getLogger('uvicorn')

# 認証コードを発行
@router.post("/auth/create", response_model=auth_schema.Auth)
async def createAuthCode(body: auth_schema.createAuthCodeParam, db: AsyncSession = Depends(get_db)):
    await common_cruds.checkIfUserExist(db, body.user_id)
    await auth_cruds.checkUser(db, body.user_id)
    return await auth_cruds.createAuthCode(db, body)

# 認証IDとコードでuser_idを取得
@router.post("/auth/authenticate", response_model=auth_schema.authenticateResponse)
async def authenticate(body: auth_schema.authenticateParam, db: AsyncSession = Depends(get_db)):    
    return await auth_cruds.authenticate(db, body)

