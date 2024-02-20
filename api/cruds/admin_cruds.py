import logging
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import mylist_model

logger = logging.getLogger('uvicorn')

async def updateReportedFlag(db: AsyncSession, original: mylist_model.MyList, activate: bool) -> mylist_model.MyList:
    if activate:
        original.reported_flag = True
    else:
        original.reported_flag = False
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original
