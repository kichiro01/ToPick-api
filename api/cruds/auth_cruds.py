import logging
import random, string
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.cruds.common_cruds import setCreateDate
from api.schemas import auth_schema
from api.models import auth_model
from datetime import datetime, timedelta
from fastapi import HTTPException

logger = logging.getLogger('uvicorn')

# 認証コードを発行
async def createAuthCode(db: AsyncSession, body: auth_schema.createAuthCodeParam) -> auth_schema.Auth:
    
    newData = auth_model.Auth(**body.model_dump())
    # 6文字のランダムな文字列を生成
    newCode = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    newData.auth_code = newCode
    setCreateDate(newData)
    db.add(newData)
    await db.commit()
    await db.refresh(newData)
    return newData

# 認証
async def authenticate(db: AsyncSession, body: auth_schema.authenticateParam) -> auth_schema.authenticateResponse:
    authInDb = await db.get(auth_model.Auth, body.auth_id)
    if not authInDb:
        logger.error(f"Auth with id {body.auth_id} not found")
        raise HTTPException(status_code=404, detail=f"Auth with id {body.auth_id} not found")
    elif authInDb.auth_code != body.auth_code:
        # 認証コードが誤っている場合
        logger.error(f"Wrong auth_code for Auth with id {body.auth_id}")
        raise HTTPException(status_code=401, detail=f"Wrong auth_code for Auth with id {body.auth_id}")
    elif (authInDb.created_at + timedelta(days=30)) < datetime.now():
        # 作成日から30日経過していた場合、認証期限切れ（レコードの削除は定期実行）
        logger.error(f"Auth with id {body.auth_id} has expired")
        raise HTTPException(status_code=401, detail=f"Auth with id {body.auth_id} has expired")
    elif authInDb.is_authenticated:
        # 認証済の場合、再認証は不可
        logger.error(f"Auth with id {body.auth_id} has already been used")
        raise HTTPException(status_code=401, detail=f"Auth with id {body.auth_id} has already been used")
    else:
        # 上記全てに当てはまらない場合のみ、認証済フラグを立て、userIdを返却する。
        authInDb.is_authenticated = True
        db.add(authInDb)
        await db.commit()
        await db.refresh(authInDb)
        return auth_schema.authenticateResponse(user_id=authInDb.user_id)
    # TODO 更新日三日経過後のデータや認証済みのデータは定期削除を検討。何らかの理由でデータ移行失敗した時用の問い合わせ動線も必要。


async def checkUser(db: AsyncSession, user_id: int):
    # ユーザーに対して有効な認証データ(※)がDB上に存在する場合、新規に認証コードを発行することはできない。
    # ※期限切れかどうかに関係なく、未認証の認証データ
    authData = await db.execute(
        select(auth_model.Auth)
        .filter(
            auth_model.Auth.user_id == user_id,
            auth_model.Auth.is_authenticated == False
        )
    )
    if len(authData.all()) != 0:
        raise HTTPException(status_code=400, detail=f"Vaild auth code for User with id {user_id} already exists")
    return
