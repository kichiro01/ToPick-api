import logging
from fastapi import APIRouter, Depends
from api.db import get_db
from api.schemas import auth as authSchema
from sqlalchemy.ext.asyncio import AsyncSession
import api.cruds.auth as authCrud
import api.cruds.common as common

router = APIRouter()
logger = logging.getLogger('uvicorn')

# 認証コードを発行
@router.post("/auth/create", response_model=authSchema.Auth)
async def createAuthCode(body: authSchema.createAuthCodeParam, db: AsyncSession = Depends(get_db)):
    await common.checkIfUserExist(db, body.user_id)
    await authCrud.checkUser(db, body.user_id)
    return await authCrud.createAuthCode(db, body)

# 認証IDとコードでuser_idを取得
@router.post("/auth/authenticate", response_model=authSchema.authenticateResponse)
async def authenticate(body: authSchema.authenticateParam, db: AsyncSession = Depends(get_db)):    
    return await authCrud.authenticate(db, body)

