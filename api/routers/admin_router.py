import logging
from fastapi import APIRouter, Depends
from api.cruds.admin_cruds import updateReportedFlag
from api.cruds.mylist_cruds import getExistMyList
from api.db import get_db
from api.schemas.mylist_schema import updateReportedFlagResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger('uvicorn')

# 通報フラグを立てる
@router.put("/reportedflag/activate/{mylist_id}", response_model=updateReportedFlagResponse)
async def activateReportedFlug(mylist_id: int, db: AsyncSession = Depends(get_db)):
    listInDb = await getExistMyList(db, mylist_id)
    return await updateReportedFlag(db, original=listInDb, activate=True)


# 通報フラグを下ろす
@router.put("/reportedflag/inactivate/{mylist_id}", response_model=updateReportedFlagResponse)
async def inactivateReportedFlug(mylist_id: int, db: AsyncSession = Depends(get_db)):
    listInDb = await getExistMyList(db, mylist_id)
    return await updateReportedFlag(db, original=listInDb, activate=False)