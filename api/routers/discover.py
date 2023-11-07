import logging
from typing import List
from fastapi import APIRouter, Depends
from api.db import get_db
from api.schemas import mylist as mylistSchema
from sqlalchemy.ext.asyncio import AsyncSession
import api.cruds.discover as discover_crud

router = APIRouter()
logger = logging.getLogger('uvicorn')

#　全ての公開マイリストを取得
@router.get("/discover/retrieve/all/", response_model=List[mylistSchema.Mylist])
async def retrieveAllMylists(db: AsyncSession = Depends(get_db)):    
    return await discover_crud.retrieveAllPublicMyList(db)
