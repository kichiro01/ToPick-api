import logging
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result
from api.models import mylist_model

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
        ).filter(
            mylist_model.MyList.is_private == False,
            mylist_model.MyList.reported_flag == False
        )
    )
    return result.all()
