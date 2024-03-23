import datetime
import logging
from typing import List, Tuple, Optional

from fastapi import HTTPException
from api.cruds import common_cruds
from api.genericCode import UpdateTargetType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result
from sqlalchemy.sql.expression import insert

from api.models import mylist_model
from api.schemas import mylist_schema
from api.models import user_model
from api.cruds import user_cruds

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
    newUser = await user_cruds.createUser(db)
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

""" v2.0以前のアプリ（iOS）でクライアント側で作成・保存されていたマイリストをDBに保存する """
async def registerCreatedList(db: AsyncSession, body: List[mylist_schema.createMylistFromRealmParam]) -> mylist_schema.createMylistFromRealmResponse:
    # ユーザー作成
    user = await user_cruds.createUser(db)
    user_id = user.user_id
    # 現在時刻取得
    now = datetime.datetime.now()
    db_items = []
    # DB保存用のマイリストデータ作成
    for myListParam in body:
        # パラメータの値をセット
        newList = mylist_model.MyList(**myListParam.model_dump())
        # 作成したユーザーIDをセット
        newList.user_id = user_id
        # 非公開、theme_typeは001で作成
        newList.theme_type = '001'
        newList.is_private = True
        newList.updated_at = now
        # db登録対象に追加
        db_items.append(newList)
    db.add_all(db_items)
    await db.commit()
    # 保存した各オブジェクトをリフレッシュ
    for item in db_items:
            await db.refresh(item)
    return mylist_schema.createMylistFromRealmResponse(
        user_id=user_id,
        my_lists=db_items
    )

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

