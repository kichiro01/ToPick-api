import logging
from typing import List, Tuple, Optional
import api.cruds.common as common
from api.genericCode import UpdateTargetType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result

import api.models.mylist as mylist_model
import api.schemas.mylist as mylist_schema
import api.models.user as user_model

logger = logging.getLogger('uvicorn')

# 全ての公開マイリストを取得
async def retrieveAllPublicMyList(db: AsyncSession) -> List[Tuple[int, str, str, dict, bool]]:
    result: Result = await db.execute(
        select(
            mylist_model.MyList.my_list_id,
            mylist_model.MyList.title,
            mylist_model.MyList.theme_type,
            mylist_model.MyList.topic,
            mylist_model.MyList.is_private
        )
    )
    return result.all()
