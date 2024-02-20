import logging
from typing import List
from api.genericCode import UpdateTargetType
from fastapi import APIRouter, Depends
from api.db import get_db
from api.schemas import mylist_schema
from sqlalchemy.ext.asyncio import AsyncSession
from api.cruds import mylist_cruds

router = APIRouter()
logger = logging.getLogger('uvicorn')

#　ユーザーの全マイリストを取得
@router.get("/mylist/retrieve/all/{user_id}", response_model=List[mylist_schema.Mylist])
async def retrieveAllMylists(user_id: int, db: AsyncSession = Depends(get_db)):    
    return await mylist_cruds.retrieveAllMyListsByUserId(db, user_id)

# 初回のマイリスト作成（ユーザー情報がないため、新規ユーザーを作成してからマイリスト作成する。）
@router.post("/mylist/create-user", response_model=mylist_schema.createUserThenMylistResponse)
async def createUserThenMyList(body: mylist_schema.createUserThenMylistParam, db: AsyncSession = Depends(get_db)):
    return await mylist_cruds.createUserAndNewList(db, body)

# 新規マイリスト作成
@router.post("/mylist/create", response_model=mylist_schema.createMylistResponse)
async def createMyList(body: mylist_schema.createMylistParam, db: AsyncSession = Depends(get_db)):
    return await mylist_cruds.createNewList(db, body)

# マイリスト更新
@router.post("/mylist/update", response_model=mylist_schema.createMylistResponse)
async def updateMyList(body: mylist_schema.updateMyListParam, db: AsyncSession = Depends(get_db)):
    mylist_id = body.my_list_id
    listInDb = await mylist_cruds.getExistMyList(db, mylist_id=mylist_id)
    return await mylist_cruds.updateMyList(db, body, original=listInDb)

# タイトル更新
@router.put("/mylist/title/{mylist_id}", response_model=mylist_schema.createMylistResponse)
async def updateTitle(mylist_id: int, body: mylist_schema.updateTitleParam, db: AsyncSession = Depends(get_db)):
    listInDb = await mylist_cruds.getExistMyList(db, mylist_id=mylist_id)
    return await mylist_cruds.updateMyListWithTarget(db, body, original=listInDb, target=UpdateTargetType.TITLE)

# テーマ更新
@router.put("/mylist/theme/{mylist_id}", response_model=mylist_schema.createMylistResponse)
async def updateTheme(mylist_id: int, body: mylist_schema.updateThemeParam, db: AsyncSession = Depends(get_db)):
    listInDb = await mylist_cruds.getExistMyList(db, mylist_id=mylist_id)
    return await mylist_cruds.updateMyListWithTarget(db, body, original=listInDb, target=UpdateTargetType.THEME)

# トピック更新
@router.put("/mylist/topic/{mylist_id}", response_model=mylist_schema.createMylistResponse)
async def updateTopic(mylist_id: int, body: mylist_schema.updateTopicParam, db: AsyncSession = Depends(get_db)):
    listInDb = await mylist_cruds.getExistMyList(db, mylist_id=mylist_id)
    return await mylist_cruds.updateMyListWithTarget(db, body, original=listInDb, target=UpdateTargetType.TOPIC)

# 非公開フラグ更新
@router.put("/mylist/privateflag/{mylist_id}", response_model=mylist_schema.createMylistResponse)
async def updatePravateFlag(mylist_id: int, body: mylist_schema.updatePrivateFlagParam, db: AsyncSession = Depends(get_db)):
    listInDb = await mylist_cruds.getExistMyList(db, mylist_id=mylist_id)
    return await mylist_cruds.updateMyListWithTarget(db, body, original=listInDb, target=UpdateTargetType.PRIVATE_FLAG)

# マイリスト削除
@router.delete("/mylist/{mylist_id}", response_model=None)
async def deleteMylist(mylist_id: int, db: AsyncSession = Depends(get_db)):
    listInDb = await mylist_cruds.getExistMyList(db, mylist_id=mylist_id)
    return await mylist_cruds.deleteMylist(db, original=listInDb)