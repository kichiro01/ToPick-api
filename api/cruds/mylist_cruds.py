import logging
from typing import List, Tuple, Optional

from fastapi import HTTPException
from api.cruds import common_cruds
from api.genericCode import UpdateTargetType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result

from api.models import mylist_model
from api.schemas import mylist_schema
from api.models import user_model

logger = logging.getLogger('uvicorn')

# 全マイリストを取得
async def retrieveAllMyListsByUserId(db: AsyncSession, user_id: int) -> List[Tuple[int, str, str, dict, bool]]:
    await common_cruds.checkIfUserExist(db, user_id)
    result: Result = await db.execute(
        select(
            mylist_model.MyList.my_list_id,
            mylist_model.MyList.title,
            mylist_model.MyList.theme_type,
            mylist_model.MyList.topic,
            mylist_model.MyList.is_private
        ).filter(mylist_model.MyList.user_id == user_id)
    )
    return result.all()

async def createUserAndNewList(db: AsyncSession, body: mylist_schema.createUserThenMylistParam) -> mylist_schema.createUserThenMylistResponse:
    # 新規ユーザー作成
    newUser = user_model.User()
    common_cruds.setCreateDate(newUser)
    db.add(newUser)
    await db.commit()
    await db.refresh(newUser)
    # 作成したユーザーのIDでマイリスト作成
    newList = createNewListFromBody(body, newUser.user_id)
    common_cruds.setCreateDate(newList)
    db.add(newList)
    await db.commit()
    await db.refresh(newList)
    return newList

async def createNewList(db: AsyncSession, body: mylist_schema.createMylistParam) -> mylist_model.MyList:
    user_id = body.model_dump()["user_id"]
    await common_cruds.checkIfUserExist(db, user_id)
    newList = mylist_model.MyList(**body.model_dump())
    common_cruds.setCreateDate(newList)
    db.add(newList)
    await db.commit()
    await db.refresh(newList)
    return newList

async def getMylistById(db: AsyncSession, mylist_id: int) -> Optional[mylist_model.MyList]:
    result: Result = await db.execute(
        select(mylist_model.MyList).filter(mylist_model.MyList.my_list_id == mylist_id)
    )
    mylist: Optional[Tuple[mylist_model.MyList]] = result.first()
    return mylist[0] if mylist is not None else None  # 要素が一つであってもtupleで返却されるので１つ目の要素を取り出す

async def updateMyList(db: AsyncSession, body: any, original: mylist_model.MyList) -> mylist_model.MyList:
    original.title = body.title
    original.theme_type = body.theme_type
    original.is_private = body.is_private
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original


async def updateMyListWithTarget(db: AsyncSession, body: any, original: mylist_model.MyList, target: UpdateTargetType) -> mylist_model.MyList:
    if target == UpdateTargetType.TITLE:
        original.title = body.title
    elif target == UpdateTargetType.THEME:
        original.theme_type = body.theme_type
    elif target == UpdateTargetType.TOPIC:
        original.topic = body.topic
    elif target == UpdateTargetType.PRIVATE_FLAG:
        original.is_private = body.is_private
    else:
        logger.error(f"UpdateTargetType with id {target} not found")
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def deleteMylist(db: AsyncSession, original: mylist_model.MyList) -> None:
    await db.delete(original)
    await db.commit()

def createNewListFromBody(body: mylist_schema.createUserThenMylistParam, user_id: int) -> mylist_model.MyList:
    dict = body.model_dump()
    # ユーザーIDがdictに含まれていない場合は登録
    dict.setdefault('user_id', user_id)
    newList = mylist_model.MyList(**dict)
    return newList

async def getExistMyList(db: AsyncSession, mylist_id: int):
    listInDb = await getMylistById(db, mylist_id=mylist_id)
    if listInDb is None: 
        logger.error(f"Mylist with id {mylist_id} not found")
        raise HTTPException(status_code=404, detail=f"Mylist with id {mylist_id} not found")
    return listInDb

