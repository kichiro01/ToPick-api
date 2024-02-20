import logging
from typing import List
from fastapi import APIRouter, Depends
from api.db import get_db
from api.schemas import mylist_schema
from sqlalchemy.ext.asyncio import AsyncSession
from api.cruds import discover_cruds

router = APIRouter()
logger = logging.getLogger('uvicorn')

#　全ての公開マイリストを取得
@router.get("/discover/retrieve/all/", response_model=List[mylist_schema.Mylist])
async def retrieveAllMylists(db: AsyncSession = Depends(get_db)):    
    return await discover_cruds.retrieveAllPublicMyList(db)
