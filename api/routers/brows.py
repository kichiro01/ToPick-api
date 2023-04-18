import logging
from typing import List
from api.genericCode import UpdateTargetType
from fastapi import APIRouter, Depends, HTTPException
from api.db import get_db
from api.schemas import mylist as mylistSchema
from sqlalchemy.ext.asyncio import AsyncSession
import api.cruds.brows as brows_crud

router = APIRouter()
logger = logging.getLogger('uvicorn')

#　全ての公開マイリストを取得
@router.get("/brows/retrieve/all/", response_model=List[mylistSchema.Mylist])
async def retrieveAllMylists(db: AsyncSession = Depends(get_db)):    
    return await brows_crud.retrieveAllPublicMyList(db)
