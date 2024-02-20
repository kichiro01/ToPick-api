from datetime import datetime
import logging
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result
from sqlalchemy.sql import text 
from api.models import theme_model

logger = logging.getLogger('uvicorn')

# 全てのデフォルトテーマを取得
async def retrieveAllPreparedTheme(db: AsyncSession) -> List[Tuple[int, str, str, str, str, dict]]:
    result: Result = await db.execute(
        select(
            theme_model.PreparedTheme.theme_id,
            theme_model.PreparedTheme.theme_type ,
            theme_model.PreparedTheme.title ,
            theme_model.PreparedTheme.description ,
            theme_model.PreparedTheme.image_type ,
            theme_model.PreparedTheme.topic
        )
    )
    return result.all()

# デフォルトテーマの最終更新日時を取得
async def retrieveLastUpdatedDate(db: AsyncSession) -> datetime:
    sql = text("SELECT MAX(updated_at) FROM prepared_theme")
    result: Result = await db.execute(sql)
    newModel = theme_model.PreparedTheme()
    newModel.updated_at = result.scalar()
    return newModel
