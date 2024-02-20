import logging
from api.cruds import common_cruds
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import user_schema
from api.models import user_model

logger = logging.getLogger('uvicorn')

async def createUser(db: AsyncSession) -> user_schema.createUserResponse:
    # 新規ユーザー作成
    newUser = user_model.User()
    common_cruds.setCreateDate(newUser)
    db.add(newUser)
    await db.commit()
    await db.refresh(newUser)
    return newUser