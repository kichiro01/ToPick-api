import logging
from typing import List
from api.genericCode import UpdateTargetType
from fastapi import APIRouter, Depends, HTTPException
from api.db import get_db
from api.schemas import mylist as mylistSchema
from sqlalchemy.ext.asyncio import AsyncSession
import api.cruds.mylist as mylist_crud

router = APIRouter()
logger = logging.getLogger('uvicorn')

#　ユーザーの全マイリストを取得
@router.get("/mylist/retrieve/all/{user_id}", response_model=List[mylistSchema.Mylist])
async def retrieveAllMylists(user_id: int, db: AsyncSession = Depends(get_db)):    
    return await mylist_crud.retrieveAllMyListsByUserId(db, user_id)

# 初回のマイリスト作成（ユーザー情報がないため、新規ユーザーを作成してからマイリスト作成する。）
@router.post("/mylist/create-user", response_model=mylistSchema.createUserThenMylistResponse)
async def createUserThenMyList(body: mylistSchema.createUserThenMylistParam, db: AsyncSession = Depends(get_db)):
    return await mylist_crud.createUserAndNewList(db, body)

# 新規マイリスト作成
@router.post("/mylist/create", response_model=mylistSchema.createMylistResponse)
async def createMyList(body: mylistSchema.createMylistParam, db: AsyncSession = Depends(get_db)):
    return await mylist_crud.createNewList(db, body)

# タイトル更新
@router.put("/mylist/title/{mylist_id}", response_model=mylistSchema.createMylistResponse)
async def updateTitle(mylist_id: int, body: mylistSchema.updateTitleParam, db: AsyncSession = Depends(get_db)):
    listInDb = await mylist_crud.getMylistById(db, mylist_id=mylist_id)
    if listInDb is None: 
        logger.error(f"Mylist with id {mylist_id} not found")
        raise HTTPException(status_code=404, detail=f"Mylist with id {mylist_id} not found")
    return await mylist_crud.updateMyList(db, body, original=listInDb, target=UpdateTargetType.TITLE)

# テーマ更新
@router.put("/mylist/theme/{mylist_id}", response_model=mylistSchema.createMylistResponse)
async def updateTheme(mylist_id: int, body: mylistSchema.updateThemeParam, db: AsyncSession = Depends(get_db)):
    listInDb = await mylist_crud.getMylistById(db, mylist_id=mylist_id)
    if listInDb is None: 
        logger.error(f"Mylist with id {mylist_id} not found")
        raise HTTPException(status_code=404, detail=f"Mylist with id {mylist_id} not found")
    return await mylist_crud.updateMyList(db, body, original=listInDb, target=UpdateTargetType.THEME)

# トピック更新
@router.put("/mylist/topic/{mylist_id}", response_model=mylistSchema.createMylistResponse)
async def updateTopic(mylist_id: int, body: mylistSchema.updateTopicParam, db: AsyncSession = Depends(get_db)):
    listInDb = await mylist_crud.getMylistById(db, mylist_id=mylist_id)
    if listInDb is None: 
        logger.error(f"Mylist with id {mylist_id} not found")
        raise HTTPException(status_code=404, detail=f"Mylist with id {mylist_id} not found")
    return await mylist_crud.updateMyList(db, body, original=listInDb, target=UpdateTargetType.TOPIC)

# 非公開フラグ更新
@router.put("/mylist/privateflag/{mylist_id}", response_model=mylistSchema.createMylistResponse)
async def updatePravateFlag(mylist_id: int, body: mylistSchema.updatePrivateFlagParam, db: AsyncSession = Depends(get_db)):
    listInDb = await mylist_crud.getMylistById(db, mylist_id=mylist_id)
    if listInDb is None: 
        logger.error(f"Mylist with id {mylist_id} not found")
        raise HTTPException(status_code=404, detail=f"Mylist with id {mylist_id} not found")
    return await mylist_crud.updateMyList(db, body, original=listInDb, target=UpdateTargetType.PRIVATE_FLAG)

# マイリスト削除
@router.delete("/mylist/{mylist_id}", response_model=None)
async def deleteMylist(mylist_id: int, db: AsyncSession = Depends(get_db)):
    listInDb = await mylist_crud.getMylistById(db, mylist_id=mylist_id)
    if listInDb is None: 
        logger.error(f"Mylist with id {mylist_id} not found")
        raise HTTPException(status_code=404, detail=f"Mylist with id {mylist_id} not found")
    return await mylist_crud.deleteMylist(db, original=listInDb)