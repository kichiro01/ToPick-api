import logging
from fastapi import APIRouter, Depends
from api.db import get_db
from api.schemas.contact_schema import contactRequestParam, reoprtRequestParam
from api.utils.mail_utils import MailUtils
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger('uvicorn')

def getUtil():
    return MailUtils()

# 意見・要望の投稿
@router.post("/contact", response_model=None)
async def recieveContact(body: contactRequestParam, util=Depends(getUtil)):
    return await util.sendContactEmail(body)

# 通報
@router.post("/report", response_model=None)
async def recieveContact(body: reoprtRequestParam, db: AsyncSession = Depends(get_db), util=Depends(getUtil)):
    return await util.sendReportEmail(db, body)