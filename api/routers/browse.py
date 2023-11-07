import logging
from typing import List
from fastapi import APIRouter, Depends
from api.db import get_db
from api.schemas import theme as themeSchema
from sqlalchemy.ext.asyncio import AsyncSession
import api.cruds.browse as browse_crud

router = APIRouter()
logger = logging.getLogger('uvicorn')

#　デフォルトテーマの全てのトピックを取得
@router.get("/browse/retrieve/theme", response_model=List[themeSchema.PreparedTheme])
async def retrieveAllPreparedThemes(db: AsyncSession = Depends(get_db)):    
    return await browse_crud.retrieveAllPreparedTheme(db)

# デフォルトテーマの最終更新日時を取得
@router.get("/browse/retrieve/last-updated-date", response_model=themeSchema.LastUpdatedDate)
async def retrieveLastUpdatedDate(db: AsyncSession = Depends(get_db)):    
    return await browse_crud.retrieveLastUpdatedDate(db)