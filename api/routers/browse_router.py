import logging
from typing import List
from fastapi import APIRouter, Depends
from api.db import get_db
from api.schemas import theme_schema
from sqlalchemy.ext.asyncio import AsyncSession
from api.cruds import browse_cruds

router = APIRouter()
logger = logging.getLogger('uvicorn')

#　デフォルトテーマの全てのトピックを取得
@router.get("/browse/retrieve/theme", response_model=List[theme_schema.PreparedTheme])
async def retrieveAllPreparedThemes(db: AsyncSession = Depends(get_db)):    
    return await browse_cruds.retrieveAllPreparedTheme(db)

# デフォルトテーマの最終更新日時を取得
@router.get("/browse/retrieve/last-updated-date", response_model=theme_schema.LastUpdatedDate)
async def retrieveLastUpdatedDate(db: AsyncSession = Depends(get_db)):    
    return await browse_cruds.retrieveLastUpdatedDate(db)