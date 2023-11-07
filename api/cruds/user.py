import logging
import api.cruds.common as common
from sqlalchemy.ext.asyncio import AsyncSession

import api.schemas.user as user_schema
import api.models.user as user_model

logger = logging.getLogger('uvicorn')

async def createUser(db: AsyncSession) -> user_schema.createUserResponse:
    # 新規ユーザー作成
    newUser = user_model.User()
    common.setCreateDate(newUser)
    db.add(newUser)
    await db.commit()
    await db.refresh(newUser)
    return newUser