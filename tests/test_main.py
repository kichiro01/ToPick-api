from datetime import timedelta
import datetime
import os
from pydantic import ValidationError
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import starlette.status
from sqlalchemy import select
from sqlalchemy.sql import text

from api.db import get_db, Base
from api.main import app

import api.models.mylist as mylist_model
import api.models.auth as auth_model
import api.models.theme as theme_model
import api.cruds.mylist as mylist_crud

ASYNC_DB_URL = "sqlite+aiosqlite:///:memory:"

class ClientWithDBSession:
    client: AsyncClient
    dbsession: AsyncSession

    def __init__(self, client, dbsession):
        self.client = client
        self.dbsession = dbsession

# テストの前準備（ジェネレータとして定義）
@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    # Async用のengineとsessionを作成
    async_engine = create_async_engine(ASYNC_DB_URL, echo=True)
    async_session = sessionmaker(
        autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
    )

    # テスト用にオンメモリのSQLiteテーブルを初期化（関数ごとにリセット）
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # DIを使ってFastAPIのDBの向き先をテスト用DBに変更
    async def get_test_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db

    # テスト用に非同期HTTPクライアントを返却
    # TODO 非同期処理がネストしているので並列で処理するように書きたい
    async with AsyncClient(app=app, base_url="http://test") as client:
        # yield client
        async with async_session() as session:
            yield ClientWithDBSession(client=client, dbsession=session)


# 【正常系】マイリスト作成(ユーザー作成)
@pytest.mark.asyncio
async def test_mylist_user_create(async_client):
    # ケース１ トピックなしで作成（新規顧客）
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": "001",
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 6
    assert response_obj["my_list_id"] == 1
    assert response_obj["title"] == "ユーザーなし作成テスト"
    assert response_obj["theme_type"] == "001"
    assert response_obj["topic"] == {"topic" : []}
    assert response_obj["is_private"] == False
    assert response_obj["user_id"] == 1

    # ケース2 1トピックありで作成（新規顧客）
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト2",
        "theme_type": "002",
        "topic": {"topic" : ["話題１"]},
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 6
    assert response_obj["my_list_id"] == 2
    assert response_obj["title"] == "ユーザーなし作成テスト2"
    assert response_obj["theme_type"] == "002"
    assert response_obj["topic"] == {"topic" : ["話題１"]}
    assert response_obj["is_private"] == False
    assert response_obj["user_id"] == 2
    # ケース3（複数トピックあり）
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト3",
        "theme_type": "002",
        "topic": {"topic" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 6
    assert response_obj["my_list_id"] == 3
    assert response_obj["title"] == "ユーザーなし作成テスト3"
    assert response_obj["theme_type"] == "002"
    assert response_obj["topic"] == {"topic" : ["話題１", "話題２", "話題３"]}
    assert response_obj["is_private"] == False
    assert response_obj["user_id"] == 3
    # ケース4（トピックが空）
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : []},
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 6
    assert response_obj["my_list_id"] == 4
    assert response_obj["title"] == "123456789012345678901234567890"
    assert response_obj["theme_type"] == "002"
    assert response_obj["topic"] == {"topic" : []}
    assert response_obj["is_private"] == False
    assert response_obj["user_id"] == 4

    # ケース5（プライベートフラグあり）
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト4",
        "theme_type": "002",
        "is_private": True
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 6
    assert response_obj["my_list_id"] == 5
    assert response_obj["title"] == "ユーザーなし作成テスト4"
    assert response_obj["theme_type"] == "002"
    assert response_obj["topic"] == {"topic" : []}
    assert response_obj["is_private"] == True
    assert response_obj["user_id"] == 5
    # ケース5_2（プライベートフラグがNone）　Noneの場合デフォでFalseが入る（Bool型のFieldの特性？）
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : ["話題１"]},
        "is_private": None
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 6
    assert response_obj["my_list_id"] == 6
    assert response_obj["title"] == "123456789012345678901234567890"
    assert response_obj["theme_type"] == "002"
    assert response_obj["topic"] == {"topic" : ["話題１"]}
    assert response_obj["is_private"] == False
    assert response_obj["user_id"] == 6

    # ケース6（マイリスト取得_正常系）
    response = await async_client.client.get("/mylist/retrieve/all/3")
    assert response.status_code == starlette.status.HTTP_200_OK
    assert response.json() == [
        {
            "my_list_id": 3,
            "title": "ユーザーなし作成テスト3",
            "theme_type": "002",
            "topic": {
                "topic": [
                    "話題１",
                    "話題２",
                    "話題３"
                ]
            },
            "is_private": False
        }
    ]

    # ケース7（マイリスト取得_異常系_存在しないユーザーID）
    response = await async_client.client.get("/mylist/retrieve/all/8")
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "User with id 8 not found"
    }

    # ケース8（マイリスト取得_異常系_ユーザーIDなし）
    response = await async_client.client.get("/mylist/retrieve/all/")
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Not Found"
    }

    # ケース9（マイリスト追加_正常系）トピックなしで追加
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 3,
        "title": "ユーザー3のマイリスト2",
        "theme_type": "003",
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 5
    assert response_obj["my_list_id"] == 7
    assert response_obj["title"] == "ユーザー3のマイリスト2"
    assert response_obj["theme_type"] == "003"
    assert response_obj["topic"] == {"topic" : []}
    assert response_obj["is_private"] == False
    # ケース10（マイリスト追加_正常系）1トピックありで作成
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 4,
        "title": "ユーザー4のマイリスト2",
        "theme_type": "003",
        "topic": {"topic" : ["話題１"]},
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 5
    assert response_obj["my_list_id"] == 8
    assert response_obj["title"] == "ユーザー4のマイリスト2"
    assert response_obj["theme_type"] == "003"
    assert response_obj["topic"] == {"topic" : ["話題１"]}
    assert response_obj["is_private"] == False

    # ケース11（マイリスト追加_正常系）複数トピックあり
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 3,
        "title": "ユーザー3のマイリスト3",
        "theme_type": "001",
        "topic": {"topic" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 5
    assert response_obj["my_list_id"] == 9
    assert response_obj["title"] == "ユーザー3のマイリスト3"
    assert response_obj["theme_type"] == "001"
    assert response_obj["topic"] == {"topic" : ["話題１", "話題２", "話題３"]}
    assert response_obj["is_private"] == False

    # ケース12（マイリスト追加_正常系）（トピックが空）
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 3,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : []},
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 5
    assert response_obj["my_list_id"] == 10
    assert response_obj["title"] == "123456789012345678901234567890"
    assert response_obj["theme_type"] == "002"
    assert response_obj["topic"] == {"topic" : []}
    assert response_obj["is_private"] == False

    # ケース13（プライベートフラグあり）
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 3,
        "title": "ユーザー3のマイリスト4",
        "theme_type": "002",
        "is_private": True
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 5
    assert response_obj["my_list_id"] == 11
    assert response_obj["title"] == "ユーザー3のマイリスト4"
    assert response_obj["theme_type"] == "002"
    assert response_obj["topic"] == {"topic" : []}
    assert response_obj["is_private"] == True
    # ケース13_2（マイリスト追加_正常系）（プライベートフラグがNone）　Noneの場合デフォでFalseが入る（Bool型のFieldの特性？）
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 3,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : ["話題１"]},
        "is_private": None
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 5
    assert response_obj["my_list_id"] == 12
    assert response_obj["title"] == "123456789012345678901234567890"
    assert response_obj["theme_type"] == "002"
    assert response_obj["topic"] == {"topic" : ["話題１"]}
    assert response_obj["is_private"] == False

    # ケース14（マイリスト取得_正常系）_複数マイリスト追加後
    response = await async_client.client.get("/mylist/retrieve/all/3")
    assert response.status_code == starlette.status.HTTP_200_OK
    assert response.json() == [
        {
            "my_list_id": 3,
            "title": "ユーザーなし作成テスト3",
            "theme_type": "002",
            "topic": {
                "topic": [
                    "話題１",
                    "話題２",
                    "話題３"
                ]
            },
            "is_private": False
        },
        {
            "my_list_id": 7,
            "title": "ユーザー3のマイリスト2",
            "theme_type": "003",
            "topic": {"topic" : []},
            "is_private": False
        },
        {
            "my_list_id": 9,
            "title": "ユーザー3のマイリスト3",
            "theme_type": "001",
            "topic": {
                "topic": [
                    "話題１",
                    "話題２",
                    "話題３"
                ]
            },
            "is_private": False
        },
        {
            "my_list_id": 10,
            "title": "123456789012345678901234567890",
            "theme_type": "002",
            "topic": {
                "topic": []
            },
            "is_private": False
        },
        {
            "my_list_id": 11,
            "title": "ユーザー3のマイリスト4",
            "theme_type": "002",
            "topic": {"topic" : []},
            "is_private": True
        },
        {
            "my_list_id": 12,
            "title": "123456789012345678901234567890",
            "theme_type": "002",
            "topic": {"topic" : ["話題１"]},
            "is_private": False
        }
    ]


# 【異常系】マイリスト作成（ユーザー作成）
@pytest.mark.asyncio
async def test_mylist_user_create_unusual(async_client):
    # ケース１ theme_typeなしで作成
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "theme_type"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    assert response.json() == expect_responce
    # ケース１_2 theme_typeをNoneで作成
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": None
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        'detail': [
            {
                'loc': [
                    'body',
                    'theme_type'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }
    assert response.json() == expect_responce
    
    # ケース2 titleなしで作成
    response = await async_client.client.post("/mylist/create-user", json={
        "theme_type": "002"
    })
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "title"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    assert response.json() == expect_responce
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    # ケース2_2 titleをNoneで作成
    response = await async_client.client.post("/mylist/create-user", json={
        "title": None,
        "theme_type": "002"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        'detail': [
            {
                'loc': [
                    'body',
                    'title'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }

    # ケース3 topicの形式が不正（topicsになっている）
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topics" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "topic dict should have a key with name 'topic'",
                "type": "value_error"
            }
        ]
    }
    assert response.json() == expect_responce
    
    # ケース4 topicの形式が不正（空の辞書）
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expect_responce

    # ケース5 topicがNone
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": None,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "topic dict should not be None",
                "type": "value_error"
            }
        ]
    }

    # ケース6 topicの辞書のvalueの型が不正
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : "配列ではない"},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "type of value for topic dict is not list",
                "type": "value_error"
            }
        ]
    }
    
    # ケース7 topicの辞書のvalueの型が不正(None)
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : None},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "type of value for topic dict is not list",
                "type": "value_error"
            }
        ]
    }
    

# 【異常系】マイリスト追加
@pytest.mark.asyncio
async def test_mylist_create_unusual(async_client):
    # ケース1 存在しないユーザーでマイリスト追加
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "test",
        "theme_type": "001",
    })
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "User with id 1 not found"
    }

    # ユーザーを作っておく
    await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": "001",
    })
    # ["my_list_id"] == 1
    # ["title"] == "ユーザーなし作成テスト"
    # ["theme_type"] == "001"
    # ["topic"] == {"topic" : []}
    # ["is_private"] == False
    # ["user_id"] == 1

    # ケース2 user_idなしで作成
    response = await async_client.client.post("/mylist/create", json={
        "title": "test",
        "theme_type": "001",
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "user_id"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    # ケース2_2 user_idをNoneで作成
    response = await async_client.client.post("/mylist/create", json={
        "user_id": None,
        "title": "ユーザーなし作成テスト",
        "theme_type": "001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        'detail': [
            {
                'loc': [
                    'body',
                    'user_id'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }
    assert response.json() == expect_responce

    # ケース3 theme_typeなしで作成
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "ユーザーなし作成テスト"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "theme_type"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    assert response.json() == expect_responce
    # ケース3_2 theme_typeをNoneで作成
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "ユーザーなし作成テスト",
        "theme_type": None
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        'detail': [
            {
                'loc': [
                    'body',
                    'theme_type'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }
    assert response.json() == expect_responce

    # ケース4 titleなしで作成
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "theme_type": "002"
    })
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "title"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    assert response.json() == expect_responce
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    # ケース4_2 titleをNoneで作成
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": None,
        "theme_type": "002"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        'detail': [
            {
                'loc': [
                    'body',
                    'title'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }
    assert response.json() == expect_responce

    # ケース5 topicの形式が不正（topicsになっている）
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topics" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "topic dict should have a key with name 'topic'",
                "type": "value_error"
            }
        ]
    }
    assert response.json() == expect_responce
    
    # ケース6 topicの形式が不正（空の辞書）
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expect_responce

    # ケース7 topicがNone
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": None,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "topic dict should not be None",
                "type": "value_error"
            }
        ]
    }

    # ケース8 topicの辞書のvalueの型が不正
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : "配列ではない"},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "type of value for topic dict is not list",
                "type": "value_error"
            }
        ]
    }
    
    # ケース9 topicの辞書のvalueの型が不正(None)
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : None},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "type of value for topic dict is not list",
                "type": "value_error"
            }
        ]
    }

    
# 【境界値】マイリスト作成（ユーザー作成）
@pytest.mark.asyncio
async def test_mylist_user_create_border(async_client):  
    # ケース1 titleが1文字未満
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "",
        "theme_type": "001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "title"
                ],
                "msg": "ensure this value has at least 1 characters",
                "type": "value_error.any_str.min_length",
                "ctx": {
                    "limit_value": 1
                }
            }
        ]
    }
    assert response.json() == expect_responce

    # ケース2 titleが1文字
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "a",
        "theme_type": "001"
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 6
    assert response_obj["my_list_id"] == 1
    assert response_obj["title"] == "a"
    assert response_obj["theme_type"] == "001"
    assert response_obj["topic"] == {"topic" : []}
    assert response_obj["is_private"] == False
    assert response_obj["user_id"] == 1

    # ケース3 titleが30文字
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "001"
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 6
    assert response_obj["my_list_id"] == 2
    assert response_obj["title"] == "123456789012345678901234567890"
    assert response_obj["theme_type"] == "001"
    assert response_obj["topic"] == {"topic" : []}
    assert response_obj["is_private"] == False
    assert response_obj["user_id"] == 2
    # ケース4 titleが31文字
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "1234567890123456789012345678901",
        "theme_type": "001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "title"
                ],
                "msg": "ensure this value has at most 30 characters",
                "type": "value_error.any_str.max_length",
                "ctx": {
                    "limit_value": 30
                }
            }
        ]
    }
    assert response.json() == expect_responce

    # ケース5 theme_typeが2文字
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "01"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "theme_type"
                ],
                "msg": "ensure this value has at least 3 characters",
                "type": "value_error.any_str.min_length",
                "ctx": {
                    "limit_value": 3
                }
            }
        ]
    }
    assert response.json() == expect_responce

    # ケース6 theme_typeが4文字
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "0001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "theme_type"
                ],
                "msg": "ensure this value has at most 3 characters",
                "type": "value_error.any_str.max_length",
                "ctx": {
                    "limit_value": 3
                }
            }
        ]
    }
    assert response.json() == expect_responce

# 【境界値】マイリスト追加
@pytest.mark.asyncio
async def test_mylist_create_border(async_client):
    # ユーザーを作っておく
    await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": "001",
    })
    # ["my_list_id"] == 1
    # ["title"] == "ユーザーなし作成テスト"
    # ["theme_type"] == "001"
    # ["topic"] == {"topic" : []}
    # ["is_private"] == False
    # ["user_id"] == 1

    # ケース1 titleが1文字未満
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "",
        "theme_type": "001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "title"
                ],
                "msg": "ensure this value has at least 1 characters",
                "type": "value_error.any_str.min_length",
                "ctx": {
                    "limit_value": 1
                }
            }
        ]
    }
    assert response.json() == expect_responce

    # ケース2 titleが1文字
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "a",
        "theme_type": "001"
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 5
    assert response_obj["my_list_id"] == 2
    assert response_obj["title"] == "a"
    assert response_obj["theme_type"] == "001"
    assert response_obj["topic"] == {"topic" : []}
    assert response_obj["is_private"] == False

    # ケース3 titleが30文字
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "001"
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 5
    assert response_obj["my_list_id"] == 3
    assert response_obj["title"] == "123456789012345678901234567890"
    assert response_obj["theme_type"] == "001"
    assert response_obj["topic"] == {"topic" : []}
    assert response_obj["is_private"] == False
    # ケース4 titleが31文字
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "1234567890123456789012345678901",
        "theme_type": "001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "title"
                ],
                "msg": "ensure this value has at most 30 characters",
                "type": "value_error.any_str.max_length",
                "ctx": {
                    "limit_value": 30
                }
            }
        ]
    }
    assert response.json() == expect_responce

    # ケース5 theme_typeが2文字
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "01"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "theme_type"
                ],
                "msg": "ensure this value has at least 3 characters",
                "type": "value_error.any_str.min_length",
                "ctx": {
                    "limit_value": 3
                }
            }
        ]
    }
    assert response.json() == expect_responce

    # ケース6 theme_typeが4文字
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "0001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "theme_type"
                ],
                "msg": "ensure this value has at most 3 characters",
                "type": "value_error.any_str.max_length",
                "ctx": {
                    "limit_value": 3
                }
            }
        ]
    }
    assert response.json() == expect_responce


# タイトル更新
@pytest.mark.asyncio
async def test_mylist_update_title(async_client):
    # ユーザーを作っておく
    await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": "001",
    })
    # ["my_list_id"] == 1
    # ["title"] == "ユーザーなし作成テスト"
    # ["theme_type"] == "001"
    # ["topic"] == {"topic" : []}
    # ["is_private"] == False
    # ["user_id"] == 1

    # 作成時点では作成日時と更新日時が同一であることを確認。
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.created_at != None and (mylistInDb.created_at == mylistInDb.updated_at)
    await async_client.dbsession.close()

    # ケース1 異常系_存在しないマイリストを更新
    response = await async_client.client.put("/mylist/title/2", json={
        "title": "test",
    })
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Mylist with id 2 not found"
    }

    # ケース2 異常系_マイリストIDなしで更新
    response = await async_client.client.put("/mylist/title/", json={
        "title": "test",
    })
    # リダイレクトされる？
    assert response.status_code == starlette.status.HTTP_307_TEMPORARY_REDIRECT
    
    # ケース3 異常系_パラメータが空
    response = await async_client.client.put("/mylist/title/1", json={})
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "title"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }

    # ケース4 異常系_パラメータなし
    response = await async_client.client.put("/mylist/title/1")
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": ["body"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    # ケース5 異常系_パラメータのキー名が不正
    response = await async_client.client.put("/mylist/title/1", json={
        "titleWrong": "test",
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "title"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }

    # ケース6 異常系_パラメータがNone
    response = await async_client.client.put("/mylist/title/1", json={
        "title": None
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': [
                    'body',
                    'title'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }

    # ケース7 境界値_１文字未満
    response = await async_client.client.put("/mylist/title/1", json={
        "title": ""
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "title"
                ],
                "msg": "ensure this value has at least 1 characters",
                "type": "value_error.any_str.min_length",
                "ctx": {
                    "limit_value": 1
                }
            }
        ]
    }

    # ケース8 境界値_31文字
    response = await async_client.client.put("/mylist/title/1", json={
        "title": "1234567890123456789012345678901"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "title"
                ],
                "msg": "ensure this value has at most 30 characters",
                "type": "value_error.any_str.max_length",
                "ctx": {
                    "limit_value": 30
                }
            }
        ]
    }
    
    # ここまでのAPI呼び出しでtitleが更新されていないことを確認
    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["title"] == "ユーザーなし作成テスト"
    # 更新日時からも確認
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.created_at != None and (mylistInDb.created_at == mylistInDb.updated_at)
    await async_client.dbsession.close()

    # ケース9 境界値_1文字
    response = await async_client.client.put("/mylist/title/1", json={
        "title": "a"
    })
    assert response.status_code == starlette.status.HTTP_200_OK

    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["title"] == "a"

    # 更新日時が更新されたことを確認。
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.title == "a"
    assert mylistInDb.created_at != None and mylistInDb.updated_at != None and (mylistInDb.created_at < mylistInDb.updated_at)
    await async_client.dbsession.close()

    # ケース10 境界値_30文字
    response = await async_client.client.put("/mylist/title/1", json={
        "title": "123456789012345678901234567890"
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    
    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["title"] == "123456789012345678901234567890"
    
# テーマ更新
@pytest.mark.asyncio
async def test_mylist_update_theme(async_client):
    # ユーザーを作っておく
    await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": "003",
    })
    # ["my_list_id"] == 1
    # ["title"] == "ユーザーなし作成テスト"
    # ["theme_type"] == "003"
    # ["topic"] == {"topic" : []}
    # ["is_private"] == False
    # ["user_id"] == 1
    
    # 作成時点では作成日時と更新日時が同一であることを確認。
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.created_at != None and (mylistInDb.created_at == mylistInDb.updated_at)
    await async_client.dbsession.close()

    # ケース1 異常系_存在しないマイリストを更新
    response = await async_client.client.put("/mylist/theme/2", json={
        "theme_type": "001",
    })
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Mylist with id 2 not found"
    }

    # ケース2 異常系_マイリストIDなしで更新
    response = await async_client.client.put("/mylist/theme/", json={
        "theme_type": "001",
    })
    # リダイレクトされる？
    assert response.status_code == starlette.status.HTTP_307_TEMPORARY_REDIRECT
    
    # ケース3 異常系_パラメータが空
    response = await async_client.client.put("/mylist/theme/1", json={})
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "theme_type"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }

    # ケース4 異常系_パラメータなし
    response = await async_client.client.put("/mylist/theme/1")
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": ["body"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    # ケース5 異常系_パラメータのキー名が不正
    response = await async_client.client.put("/mylist/theme/1", json={
        "theme_typeWrong": "001",
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "theme_type"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }

    # ケース6 異常系_パラメータがNone
    response = await async_client.client.put("/mylist/theme/1", json={
        "theme_type": None
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': [
                    'body',
                    'theme_type'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }

    # ケース7 境界値_3文字未満
    response = await async_client.client.put("/mylist/theme/1", json={
        "theme_type": "01"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "theme_type"
                ],
                "msg": "ensure this value has at least 3 characters",
                "type": "value_error.any_str.min_length",
                "ctx": {
                    "limit_value": 3
                }
            }
        ]
    }

    # ケース8 境界値_4文字
    response = await async_client.client.put("/mylist/theme/1", json={
        "theme_type": "0001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "theme_type"
                ],
                "msg": "ensure this value has at most 3 characters",
                "type": "value_error.any_str.max_length",
                "ctx": {
                    "limit_value": 3
                }
            }
        ]
    }
    
    # ここまでのAPI呼び出しでtitleが更新されていないことを確認
    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["theme_type"] == "003"
    # 更新日時からも確認
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.created_at != None and (mylistInDb.created_at == mylistInDb.updated_at)
    await async_client.dbsession.close()

    # ケース9 正常系_3文字
    response = await async_client.client.put("/mylist/theme/1", json={
        "theme_type": "002"
    })
    assert response.status_code == starlette.status.HTTP_200_OK

    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["theme_type"] == "002"

    # 更新日時が更新されたことを確認。
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.theme_type == "002"
    assert mylistInDb.created_at != None and mylistInDb.updated_at != None and (mylistInDb.created_at < mylistInDb.updated_at)
    await async_client.dbsession.close()
    
# トピック更新
@pytest.mark.asyncio
async def test_mylist_update_topic(async_client):
    # ユーザーを作っておく
    await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": "003",
        "topic": {"topic" : ["話題１"]}
    })
    # ["my_list_id"] == 1
    # ["title"] == "ユーザーなし作成テスト"
    # ["theme_type"] == "003"
    # ["topic"] == {"topic" : ["話題１"]}
    # ["is_private"] == False
    # ["user_id"] == 1

    # 作成時点では作成日時と更新日時が同一であることを確認。
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.created_at != None and (mylistInDb.created_at == mylistInDb.updated_at)
    await async_client.dbsession.close()
    
    # ケース1 異常系_存在しないマイリストを更新
    response = await async_client.client.put("/mylist/topic/2", json={
        "topic": {"topic" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Mylist with id 2 not found"
    }

    # ケース2 異常系_マイリストIDなしで更新
    response = await async_client.client.put("/mylist/topic/", json={
        "topic": {"topic" : ["話題１", "話題２", "話題３"]},
    })
    # リダイレクトされる？
    assert response.status_code == starlette.status.HTTP_307_TEMPORARY_REDIRECT
    
    # ケース3 異常系_パラメータが空
    response = await async_client.client.put("/mylist/topic/1", json={})
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }

    # ケース4 異常系_パラメータなし
    response = await async_client.client.put("/mylist/topic/1")
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": ["body"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    # ケース5 異常系_パラメータのキー名が不正
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic_typeWrong": {"topic" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }

    # ケース6 異常系_パラメータがNone
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": None,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': [
                    'body',
                    'topic'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }

    # ケース7 異常系_topicの形式が不正（topicsになっている）
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": {"topics" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    expect_responce = {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "topic dict should have a key with name 'topic'",
                "type": "value_error"
            }
        ]
    }
    assert response.json() == expect_responce
    
    # ケース8 異常系_topicの形式が不正（空の辞書）
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": {},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == expect_responce

    # ケース9 topicの辞書のvalueの型が不正
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": {"topic" : "配列ではない"},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "type of value for topic dict is not list",
                "type": "value_error"
            }
        ]
    }
    
    # ケース10 topicの辞書のvalueの型が不正(None)
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": {"topic" : None},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "topic"
                ],
                "msg": "type of value for topic dict is not list",
                "type": "value_error"
            }
        ]
    }

    # ここまでのAPI呼び出しでtopicが更新されていないことを確認
    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["topic"] == {"topic" : ["話題１"]}
    # 更新日時からも確認
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.created_at != None and (mylistInDb.created_at == mylistInDb.updated_at)
    await async_client.dbsession.close()

    # ケース11 正常系_1トピックに更新
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": {"topic" : ["話題2"]},
    })
    assert response.status_code == starlette.status.HTTP_200_OK

    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["topic"] == {"topic" : ["話題2"]}

    # 更新日時が更新されたことを確認。
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.topic == {"topic" : ["話題2"]}
    assert mylistInDb.created_at != None and mylistInDb.updated_at != None and (mylistInDb.created_at < mylistInDb.updated_at)
    await async_client.dbsession.close()

    # ケース12 正常系_複数トピックに更新（増やす）
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": {"topic" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_200_OK

    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["topic"] == {"topic" : ["話題１", "話題２", "話題３"]}
    
    # ケース13 正常系_トピックを空に更新（減らす）
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": {"topic" : []},
    })
    assert response.status_code == starlette.status.HTTP_200_OK

    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["topic"] == {"topic" : []}

# 非公開フラグ更新
@pytest.mark.asyncio
async def test_mylist_update_privateFlag(async_client):
    # ユーザーを作っておく
    await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": "003",
    })
    # ["my_list_id"] == 1
    # ["title"] == "ユーザーなし作成テスト"
    # ["theme_type"] == "003"
    # ["topic"] == {"topic" : []}
    # ["is_private"] == False
    # ["user_id"] == 1

    # 作成時点では作成日時と更新日時が同一であることを確認。
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.created_at != None and (mylistInDb.created_at == mylistInDb.updated_at)
    await async_client.dbsession.close()
    
    # ケース1 異常系_存在しないマイリストを更新
    response = await async_client.client.put("/mylist/privateflag/2", json={
        "is_private": True,
    })
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Mylist with id 2 not found"
    }

    # ケース2 異常系_マイリストIDなしで更新
    response = await async_client.client.put("/mylist/privateflag/", json={
        "is_private": True,
    })
    # リダイレクトされる？
    assert response.status_code == starlette.status.HTTP_307_TEMPORARY_REDIRECT
    
    # ケース3 異常系_パラメータが空
    response = await async_client.client.put("/mylist/privateflag/1", json={})
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "is_private"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }

    # ケース4 異常系_パラメータなし
    response = await async_client.client.put("/mylist/privateflag/1")
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": ["body"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    # ケース5 異常系_パラメータのキー名が不正
    response = await async_client.client.put("/mylist/privateflag/1", json={
        "is_privateWrong": True,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "is_private"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }

    # ケース6 異常系_パラメータがNone
    response = await async_client.client.put("/mylist/privateflag/1", json={
        "is_private": None,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': [
                    'body',
                    'is_private'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }
    
    # ここまでのAPI呼び出しでtitleが更新されていないことを確認
    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["is_private"] == False
    # 更新日時からも確認
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.created_at != None and (mylistInDb.created_at == mylistInDb.updated_at)
    await async_client.dbsession.close()

    # ケース7 正常系_TRUEで更新
    response = await async_client.client.put("/mylist/privateflag/1", json={
        "is_private": True
    })
    assert response.status_code == starlette.status.HTTP_200_OK

    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["is_private"] == True

    # 更新日時が更新されたことを確認。
    mylistInDb = await async_client.dbsession.get(mylist_model.MyList, 1)
    assert mylistInDb.is_private == True
    assert mylistInDb.created_at != None and mylistInDb.updated_at != None and (mylistInDb.created_at < mylistInDb.updated_at)
    await async_client.dbsession.close()

    # ケース8 正常系_TRUEで更新(同じ値で更新)
    response = await async_client.client.put("/mylist/privateflag/1", json={
        "is_private": True
    })
    assert response.status_code == starlette.status.HTTP_200_OK

    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["is_private"] == True

    # ケース9 正常系_FALSEで更新(違う値で更新)
    response = await async_client.client.put("/mylist/privateflag/1", json={
        "is_private": False
    })
    assert response.status_code == starlette.status.HTTP_200_OK

    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert myListInDb.json()[0]["is_private"] == False


# マイリスト削除
@pytest.mark.asyncio
async def test_mylist_delete(async_client):
    # ユーザーを作っておく
    await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": "003",
    })
    # ["my_list_id"] == 1
    # ["title"] == "ユーザーなし作成テスト"
    # ["theme_type"] == "003"
    # ["topic"] == {"topic" : []}
    # ["is_private"] == False
    # ["user_id"] == 1
    
    # ケース1 異常系_存在しないマイリストを削除
    response = await async_client.client.delete("/mylist/2")
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Mylist with id 2 not found"
    }

    # ケース2 異常系_マイリストIDなしで削除
    response = await async_client.client.delete("/mylist/")
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Not Found"
    }
    
    # ここまでのAPI呼び出しでマイリストが削除されていないことを確認
    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert len(myListInDb.json()) == 1

    # ケース3 正常系_削除
    response = await async_client.client.delete("/mylist/1")
    assert response.status_code == starlette.status.HTTP_200_OK
    # 削除後、ユーザーのマイリスト一覧は空
    myListInDb = await async_client.client.get("/mylist/retrieve/all/1")
    assert myListInDb.status_code == starlette.status.HTTP_200_OK
    assert len(myListInDb.json()) == 0
    assert myListInDb.json() == []

    # ケース4 異常系_削除済みのマイリストID（存在しないマイリスト）で削除
    response = await async_client.client.delete("/mylist/１")
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Mylist with id 1 not found"
    }

# 異常系_全マイリスト取得
@pytest.mark.asyncio
async def test_mylist_retrieve_validation(async_client):
    # test_mylist_user_createのケース7,8で存在しないユーザーへの取得、
    # test_mylist_deleteのケース3で存在するユーザーのマイリストが0件の場合のテストは実施済
    # ⇨このシナリオでは、DBを直にいじって不正なデータを作り、マイリスト取得時の各項目のバリデーションのテストを行う。
    
    # ユーザーを作っておく
    await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": "003",
    })
    # ["my_list_id"] == 1
    # ["title"] == "ユーザーなし作成テスト"
    # ["theme_type"] == "003"
    # ["topic"] == {"topic" : []}
    # ["is_private"] == False
    # ["user_id"] == 1

    # ケース1_title文字数下限違反
    original = await mylist_crud.getMylistById(async_client.dbsession, mylist_id=1)
    original.title = ""
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> title" in str(e.value)
    assert "ensure this value has at least 1 characters (type=value_error.any_str.min_length; limit_value=1)" in str(e.value)
    # {'loc': ('response', 0, 'title'), 'msg': 'ensure this value has at least 1 characters', 'type': 'value_error.any_str.min_length', 'ctx': {'limit_value': 1}}

    # ケース2_title文字数上限違反
    # タイトルを入れ直す
    original.title = "1234567890123456789012345678901"
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> title" in str(e.value)
    assert "ensure this value has at most 30 characters (type=value_error.any_str.max_length; limit_value=30)" in str(e.value)

    # ケース3_titleがNone
    original.title = None
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> title" in str(e.value)
    assert "none is not an allowed value (type=type_error.none.not_allowed)" in str(e.value)
    # titleをもとに戻しておく。
    original.title = 'ユーザーなし作成テスト'
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    
    # ケース4 theme_type下限違反
    original.theme_type = "01"
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> theme_type" in str(e.value)
    assert "ensure this value has at least 3 characters (type=value_error.any_str.min_length; limit_value=3)" in str(e.value)
    
    # ケース5 theme_type上限違反
    original.theme_type = "0001"
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> theme_type" in str(e.value)
    assert "ensure this value has at most 3 characters (type=value_error.any_str.max_length; limit_value=3)" in str(e.value)

    # ケース6 theme_typeがNone
    original.theme_type = None
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> theme_type" in str(e.value)
    assert "none is not an allowed value (type=type_error.none.not_allowed)" in str(e.value)
    # theme_typeをもとに戻しておく。
    original.theme_type = '003'
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()

    # ケース7 topicの形式が不正（キー名がtopicではない(topicsになっている)）
    original.topic = {"topics" : ["話題１", "話題２", "話題３"]}
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> topic" in str(e.value)
    assert "topic dict should have a key with name 'topic' (type=value_error)" in str(e.value)
    
    # ケース8 topicの形式が不正（空の辞書）
    original.topic = {}
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> topic" in str(e.value)
    assert "topic dict should have a key with name 'topic' (type=value_error)" in str(e.value)
    
    # ケース9 topicがNone
    original.topic = None
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> topic" in str(e.value)
    assert "none is not an allowed value (type=type_error.none.not_allowed)" in str(e.value)

    # ケース10 topicの辞書のvalueの型が不正
    original.topic = {"topic" : "配列ではない"}
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> topic" in str(e.value)
    assert "type of value for topic dict is not list" in str(e.value)

    # ケース11 topicの辞書のvalueの型が不正(None)
    original.topic = {"topic" : None}
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> topic" in str(e.value)
    assert "type of value for topic dict is not list" in str(e.value)
    # topicをもとに戻しておく。
    original.topic = {"topic" : []}
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()

    # ケース12 非公開フラグがNone
    original.is_private = None
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    assert "1 validation error for Mylist" in str(e.value)
    assert "response -> 0 -> is_private" in str(e.value)
    assert "none is not an allowed value (type=type_error.none.not_allowed)" in str(e.value)

#################################################################################################
#############################認証関連のテスト#########################################################
#################################################################################################

# 認証コード発行
@pytest.mark.asyncio
async def test_auth_create(async_client):
    # ケース1 異常系_存在しないユーザーの認証コード発行
    response = await async_client.client.post("/auth/create", json={
        "user_id": 1,
    })
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "User with id 1 not found"
    }

    # ユーザーを作っておく
    await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": "001",
    })
    # ["my_list_id"] == 1
    # ["title"] == "ユーザーなし作成テスト"
    # ["theme_type"] == "001"
    # ["topic"] == {"topic" : []}
    # ["is_private"] == False
    # ["user_id"] == 1
    
    # ケース2 異常系_パラメータが空
    response = await async_client.client.post("/auth/create", json={})
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "user_id"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }

    # ケース3 異常系_パラメータなし
    response = await async_client.client.post("/auth/create")
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": ["body"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    # ケース4 異常系_パラメータのキー名が不正
    response = await async_client.client.post("/auth/create", json={
        "user_idWrong": 1,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "user_id"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }

    # ケース5 異常系_パラメータがNone
    response = await async_client.client.post("/auth/create", json={
        "user_id": None,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': [
                    'body',
                    'user_id'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }
    
    # ここまでのAPI呼び出しで認証コードが作成されていないことを確認
    AuthRecords = await async_client.dbsession.execute(select(auth_model.Auth))
    assert len(AuthRecords.all()) == 0
    await async_client.dbsession.close()

    # ケース6 正常系_認証コード作成
    response = await async_client.client.post("/auth/create", json={
        "user_id": 1,
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    assert "'auth_id': 1" in str(response.json())
    assert "'auth_code':" in str(response.json())
    # 後の認証のテストのために認証コードを変数に格納しておく
    codeValue = response.json()["auth_code"]
    # DBを直接確認する
    AuthRecords = await async_client.dbsession.execute(select(auth_model.Auth))
    assert len(AuthRecords.all()) == 1
    await async_client.dbsession.close()
    # 作成時点では登録日時、変更日時が同じ
    authRecord = await async_client.dbsession.get(auth_model.Auth, 1)
    assert authRecord.created_at != None and (authRecord.created_at == authRecord.updated_at)
    await async_client.dbsession.close()

    # ケース7 認証_正常系_存在しない認証ID
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 2,
        "auth_code": codeValue
    })
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Auth with id 2 not found"
    }

    # ケース8 認証_異常系_パラメータなし
    response = await async_client.client.post("/auth/authenticate")
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": ["body"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    # ケース9 認証_異常系_パラメータが空
    response = await async_client.client.post("/auth/authenticate", json={})
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "auth_id"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            },
            {
                "loc": [
                    "body",
                    "auth_code"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    # ケース10 認証_異常系_パラメータのキー名が不正_認証ID
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_idWrong": 1,
        "auth_code": codeValue
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "auth_id"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }

    # ケース11 認証_異常系_パラメータのキー名が不正_認証コード
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1,
        "auth_codeWrong": codeValue
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "auth_code"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    # ケース12 認証_異常系_パラメータがNone_認証ID
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": None,
        "auth_code": codeValue
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': [
                    'body',
                    'auth_id'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }
    # ケース13 認証_異常系_パラメータがNone_認証コード
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1,
        "auth_code": None
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': [
                    'body',
                    'auth_code'
                ],
                'msg': 'none is not an allowed value',
                'type': 'type_error.none.not_allowed'
            }
        ]
    }
    # ケース14 認証_異常系_パラメータ不足_認証ID
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_code": codeValue
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "auth_id"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    # ケース15 認証_異常系_パラメータ不足_認証コード
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "auth_code"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    # ケース16 認証_正常系_認証コードが6桁未満
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1,
        "auth_code": 'abc12'
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "auth_code"
                ],
                "msg": "ensure this value has at least 6 characters",
                "type": "value_error.any_str.min_length",
                "ctx": {
                    "limit_value": 6
                }
            }
        ]
    }
    # ケース17 認証_正常系_認証コードが7桁以上
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1,
        "auth_code": 'abc1234'
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "auth_code"
                ],
                "msg": "ensure this value has at most 6 characters",
                "type": "value_error.any_str.max_length",
                "ctx": {
                    "limit_value": 6
                }
            }
        ]
    }
    # ケース18 認証_正常系_認証コード不一致(6桁) （実際に生成されるコードに数字は含まれないため下記は必ず不一致となる。）
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1,
        "auth_code": 'abc123'
    })
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": 'Wrong auth_code for Auth with id 1'}

    # ここまででユーザーが認証されていないこと、更新日時が更新されていないことを確認。
    authRecord = await async_client.dbsession.get(auth_model.Auth, 1)
    assert authRecord.is_authenticated == False
    assert authRecord.created_at != None and (authRecord.created_at == authRecord.updated_at)
    await async_client.dbsession.close()

    # ケース19 認証_正常系_未認証のコードがある状態で同じユーザーで新規に認証コード発行
    response = await async_client.client.post("/auth/create", json={
        "user_id": 1,
    })
    # 既に認証コードがあるので400を返却
    assert response.status_code == starlette.status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Vaild auth code for User with id 1 already exists"
    }
    # 認証コードは作成されていない
    AuthRecords = await async_client.dbsession.execute(select(auth_model.Auth))
    assert len(AuthRecords.all()) == 1
    await async_client.dbsession.close()

    # ケース20 認証_正常系_認証成功
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1,
        "auth_code": codeValue
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    assert response.json() == {
        "user_id": 1
    }
    # DBで認証済みになっていること。データ更新時に更新日時も一緒に更新されていることまで確認。
    authRecord = await async_client.dbsession.get(auth_model.Auth, 1)
    assert authRecord.is_authenticated == True
    assert authRecord.created_at != None and authRecord.updated_at != None and (authRecord.created_at < authRecord.updated_at)
    await async_client.dbsession.close()
    
    # ケース21 認証_正常系_認証済のIDで再認証不可
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1,
        "auth_code": codeValue
    })
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": 'Auth with id 1 has already been used'
    }
    
    # ケース22 認証_正常系_同じユーザーに対する認証コードが存在していても、認証済の場合は新規に認証コード発行可能
    response = await async_client.client.post("/auth/create", json={
        "user_id": 1,
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    assert "'auth_id': 2" in str(response.json())
    assert "'auth_code':" in str(response.json())
    # 後の認証のテストのために認証コードを変数に格納しておく
    codeValue = response.json()["auth_code"]
    # DBを直接確認する
    AuthRecords = await async_client.dbsession.execute(select(auth_model.Auth))
    assert len(AuthRecords.all()) == 2
    await async_client.dbsession.close()
    # 作成時点では登録日時、変更日時が同じ
    authRecord = await async_client.dbsession.get(auth_model.Auth, 2)
    assert authRecord.created_at != None and (authRecord.created_at == authRecord.updated_at)
    await async_client.dbsession.close()
    
    # ケース23 認証_正常系_認証コード期限切れ（境界値）
    # 作成日時を30日前にしておく
    original = await async_client.dbsession.get(auth_model.Auth, 2)
    # 元の日時を保管
    original_created_datetime = original.created_at
    original_updated_datetime = original.updated_at
    # 30日前に設定
    original.created_at = original_created_datetime - timedelta(days=30)
    original.updated_at = original_updated_datetime - timedelta(days=30)
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 2,
        "auth_code": codeValue
    })
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": 'Auth with id 2 has expired'
    }
    # ユーザーが認証されていないことを確認。
    authRecord = await async_client.dbsession.get(auth_model.Auth, 2)
    assert authRecord.is_authenticated == False
    await async_client.dbsession.close()

    # ケース24 認証_正常系_認証コード期限内（境界値）
    # 作成日時を29日前にしておく
    original.created_at = original_created_datetime - timedelta(days=29)
    original.updated_at = original_updated_datetime - timedelta(days=29)
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # 作成日時と更新日時は同一
    assert authRecord.created_at != None and (authRecord.created_at == authRecord.updated_at)

    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 2,
        "auth_code": codeValue
    })
    assert response.status_code == starlette.status.HTTP_200_OK
    assert response.json() == {
        "user_id": 1
    }
    # DBで認証済みになっていること。データ更新時に更新日時も一緒に更新されていることまで確認。
    authRecord = await async_client.dbsession.get(auth_model.Auth, 2)
    assert authRecord.is_authenticated == True
    assert authRecord.created_at != None and authRecord.updated_at != None and (authRecord.created_at < authRecord.updated_at)
    await async_client.dbsession.close()

#################################################################################################
#############################デフォルトテーマ取得のテスト#########################################################
#################################################################################################

# 【正常系】デフォルトテーマの全てのトピックを取得
@pytest.mark.asyncio
async def test_retrieve_all_prepared_theme(async_client):
    # デフォルトテーマをインサート
    sqlstr = \
    'INSERT INTO '\
    'prepared_theme(theme_type, title, `description`, image_type, topic, created_at, updated_at) '\
    'VALUES '\
    '(\"001\", \"一般\", \"困った時はこれ！\", \"001\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"落ち着く空間\",\"秋といえば？\",\"趣味\",\"今会いたい人\",\"オススメのレストラン\",\"こんな癖があります\",\"特技\",\"ハメを外してやってみたいこと\",\"好きなスポーツ\",\"これについてなら語れる！\",\"好きな映画\",\"家ではどんな格好？\",\"好きなコンビニ\",\"生まれ変わるなら男？女？\",\"一日だけ異性になれるなら何する？\",\"オススメの音楽\",\"オススメのアプリ\",\"最高のご飯のお供\",\"自分の地元をPR!\",\"最近のお気に入り写真\",\"私服のこだわり\",\"遊びでよく行くエリア\",\"得意なモノマネ\",\"苦手なもの\",\"マイブーム\",\"理想の旅行プラン\",\"一ヶ月の休暇があるならどう使う？\",\"一億円あったらどう使う？\",\"私のお金の使い道・使い方\",\"好きな匂い\",\"ケータイのホーム画面公開！\",\"睡眠のこだわり\",\"休日の過ごし方\",\"朝方？夜型？\",\"健康のために心がけていること\",\"好きな場所\",\"至福のひと時\",\"昔からの宝物\",\"実家の独自文化\",\"得意料理\",\"好きなものは先食べる派？\",\"電車の中ってどう過ごす？\",\"こういう人が許せない\",\"好きなブランド\",\"犬派？猫派？\",\"自分を動物に例えるなら\",\"最近ハッピーだったこと\",\"最近見た夢\",\"起きて最初にすること\",\"カラオケの十八番\",\"風邪の自分なりの治療法\",\"自分なりのゲンかつぎ\",\"もし一つだけ魔法がつかえるなら\",\"無人島に一つだけ持っていくなら\",\"一日に鏡を見る回数\",\"今週末の予定\",\"生活の中のこだわり\",\"携帯と財布以外の必需品\",\"行ってみたい国\",\"好きな芸能人\",\"好きな季節\",\"髪を染めたことはある？\",\"好きな時代に行けるなら\",\"一年前の今頃何してた？\",\"家で一人の時何をする？\",\"歌詞を覚えている曲は？\",\"私って何の人で認識されてますか？\",\"過去最高の褒め言葉\",\" 落ちてるお金いくらまでなら拾う？\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"001\", \"恋愛\", \"盛り上がる恋バナを用意しました\", \"002\", JSON_OBJECT(\"topic\",JSON_ARRAY(\"好きな異性のタイプ\",\"異性の好きな髪型\",\"理想のデートプラン\",\"浮気についてどう思う？\",\"どきっとする一言\",\"異性の好きな服装/無理な服装\",\"異性の好きな仕草\",\"追いかけたい？追いかけられたい？\",\"バレンタインの思い出\",\"束縛はアリ？ナシ？\",\"好きな人にどうアプローチする？\",\"あなたの恋愛スタイル\",\"好きな人への返信速度\",\"好きな人に出てしまう態度\",\"ファーストキスの思い出\",\"初恋の人について\",\"デートのお会計は割り勘？\",\"異性にモノ申す！\",\"好きなのは草食系？肉食系？\",\"キスは付き合ってからどれくらいが理想？\",\"私の恋愛履歴\",\"ベストな別れ方とは\",\"衝撃的だった異性の言動\",\"好きな人に恋人がいたらどうする？\",\"友達と好きな人がかぶったらどうする？\",\"恋人を家族に紹介する？\",\"恋人の家に行ってチェックしてしまうところ\",\"あなたは恋愛体質？\",\"元カレ/元カノとの別れ方\",\"結婚対象になる恋人とは？\",\"恋人へのプレゼントにいくらかける？\",\"恋愛において一番幸せな瞬間/期間\",\"恋人への不満は言えるほう？\",\"恋人の前での自分はどんな感じ？\",\"恋愛相談できる友達の数\",\"恋人に求めるもの\",\"恋人の条件（こんな人と付き合いたい）\",\"理想のプロポーズ \")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"001\", \"人生\", \"少し深い話をしたい時に\", \"003\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"座右の銘\",\"５０歳の時どうなっていたい？\",\"何歳までに結婚したい？\",\"人生最大の失敗\",\"自分のコンプレックス\",\"最近泣いたのはいつ？\",\"どんな人生の最期を迎えたい？\",\"人間は死後、どうなると思う？\",\"人生最大のチャレンジ\",\"人生で一番の親友\",\"尊敬する人\",\"今の目標\",\"今の一番の悩み\",\"一年前の今頃何してた？\",\"誰にもいえない秘密はある？\",\"こんな人間でありたい\",\"お世話になった人\",\"動物に生まれ変わるなら何になりたい？\",\"生活の中のこだわり\",\"仕事と私生活の理想的なバランス\",\"覚えている一番小さい頃の思い出\",\"人生で一番辛かったこと\",\"過去最高の褒め言葉\",\"もらった中で一番のプレゼント\",\"小さい頃の夢\",\"過去一番高額な買い物\",\"明日死ぬなら何をする？\",\"好きな名言\",\"昔からの宝物\",\"好きな人に恋人がいたらどうする？\",\"友達と好きな人がかぶったらどうする？\",\"最後に喧嘩したのはいつ？\",\"過去最大のサプライズ\",\"何歳まで生きたい？\",\"自分の人生のピークはいつだと思う？\",\"大切にしている信念\",\"十代の自分への助言\",\"１０年後の自分はどうありたい？\",\"子供ができたらどう育てたい？\",\"子供につけたい名前\",\"最近の失敗エピソード\",\"一億円あったらどう使う？\",\"すべらない話\",\"一日の内SNSにどれくらい時間使う？\",\"1番出会えてよかった人間\",\"理想のプロポーズ \")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"001\", \"学校\", \"たまには過去を懐かしむのも良いですね\", \"004\", JSON_OBJECT(\"topic\",  JSON_ARRAY(\"昔学校で流行った遊び\",\"昔学校で流行った言葉\",\"好きだった給食\",\"喧嘩した思い出\",\"学校の謎ルール\",\"小学校あるある\",\"印象に残っている先生\",\"休み時間の過ごし方\",\"学校のお気に入りの場所\",\"中学生活を一言で表すと？\",\"一番強かった不良\",\"好きだった授業\",\"得意科目\",\"学生生活最大の怪我・危機\",\"青春を感じた瞬間\",\"卒業式は泣いた？\",\"学校でいちばん思い出に残っている行事\",\"授業をサボったことは？\",\"入っていた部活\",\"寮、一人暮らし、実家のうち理想は？\",\"これからの進路について\",\"学生のうちにやっておきたいこと\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"001\", \"友達\", \"友達の友達で面白い人がきっといます\", \"005\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"一番面白い友達の話\",\"一番友情を感じた瞬間\",\"一番尊敬する友達\",\"一番の親友の好きなところ\",\"友達に鼻毛出てるって言える？\",\"友達に何円までなら貸せる？\",\"友達に借りた最高額\",\"親友と言える人の人数\",\"友達と親友の違いとは\",\"ラインの友達何人いる？\",\"友達の条件\",\"男女間の友情って成立する？\",\"こういう友達が欲しい\",\"友達につけられたあだ名\",\"友達へのプレゼントにかけた最高額\",\"友達と好きな人がかぶったらどうする？\",\"誕生日覚えてる友達の数？\",\"友達とルームシェアできる？\",\"友達の影響で買ったもの\",\"恋愛相談できる友達の数\",\"この人にはお世話になった\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"001\", \"真面目\", \"真面目な話ができる友達って良いですよね\", \"006\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"時事問題やニュースで気になっていること\",\"オススメの本\",\"注目している業界\",\"自分を高めるためにしている習慣\",\"日本の良いところ・悪いところ\",\"SNSの功罪\",\"３０年後の世界を予想\",\"環境問題でいちばん深刻だと思うこと\",\"疑問を持っているルール・制度・風潮\",\"安楽死と死刑について\",\"２１世紀に求められるスキルとは\",\"永遠の何歳でいたい？\",\"友人と集まった時、中心となる話題は？\",\"老後をどう過ごしたいか\",\"自分なりのリフレッシュ法\",\"自分を色に例えるなら\",\"大切にしている信念\",\"自分の人生のピークはいつだと思う？\",\"生活の中で最も優先順位が高いのは？\",\"学生時代にしておくべきこと\",\"今の自分に足りないもの\",\"仕事と私生活の理想的なバランス\",\"一年前の今頃何してた？\",\"十代の自分への助言\",\"１０年後の自分はどうありたい？\",\"人生でいちばん頑張ったこと\",\"自分の悪い癖\",\"子供の教育について\",\"結果とプロセスどちらが大事だと思う？\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"002\", \"飲み会\", \"飲み会の途中でスマホいじるってよくありますよね\", \"007\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"好きなお酒\",\"酔うとどうなる？\",\"お酒の失敗エピソード\",\"自分なりのゲンかつぎ\",\"最近ハッピーだったこと\",\"最強の酒の肴\",\"カラオケの十八番\",\"オススメの音楽\",\"オススメアプリ\",\"最近のお気に入り写真\",\"家ではどんな格好？\",\"好きなコンビニ\",\"最近失敗した話\",\"至福のひと時\",\"私服のこだわり\",\"遊びでよく行くエリア\",\"得意なモノマネ\",\"苦手なもの\",\"理想の旅行プラン\",\"一ヶ月の休暇があるならどう使う？\",\"一億円あったらどう使う？\",\"私のお金の使い道・使い方\",\"ケータイのホーム画面公開！\",\"異性の好きな仕草\",\"健康のために心がけていること\",\"好きな場所\",\"実家の独自文化\",\"得意料理\",\"マイブーム\",\"電車の中ってどう過ごす？\",\"こういう人が許せない\",\"あえて自分からは言ってない秘密\",\"最近見た夢\",\"起きて最初にすること\",\"もし一つだけ魔法がつかえるなら\",\"無人島に一つだけ持っていくなら\",\"今週末の予定\",\"生活の中のこだわり\",\"携帯と財布以外の必需品\",\"一年前の今頃何してた？\",\"十代の自分への助言\",\"今の気持ちを川柳で\",\"過去最高の褒め言葉\",\"歌詞を覚えている曲は？\",\"私って何の人で認識されてますか？\",\" 落ちてるお金いくらまでなら拾う？\",\"好きな人に恋人がいたらどうする？\",\"友達と好きな人がかぶったらどうする？\",\"ハメを外してやってみたいこと\",\"フェチ\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"002\", \"合コン\", \"初対面の男女って何を話したら良いんでしょうか\", \"008\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"好きなお酒\",\"どきっとする一言\",\"好きな異性のタイプ\",\"理想のデートプラン\",\"異性の好きな服装\",\"異性の好きな仕草\",\"マイブーム\",\"得意料理\",\"メンバーの兄弟の数を当てる\",\"５０歳の時どうなっていたい？\",\"家で一人の時何をする？\",\"好きな食べ物\",\"実家の独自文化\",\"髪を染めたことはある？\",\"電車の中ってどう過ごす？\",\"最近見た夢\",\"起きて最初にすること\",\"もし一つだけ魔法がつかえるなら\",\"無人島に一つだけ持っていくなら\",\"生活の中のこだわり\",\"至福のひと時\",\"ケータイのホーム画面公開！\",\"インドア派？アウトドア派？\",\"最近ハッピーだったこと\",\"カラオケの十八番\",\"家ではどんな格好？\",\"遊びでよく行くエリア\",\"異性のメンバーを褒める！\",\"苦手なもの\",\"これについてなら語れる！\",\"好きな季節\",\"好きなブランド\",\"電車の中ってどう過ごす？\",\"追いかけたい？追いかけられたい？\",\"束縛はアリ？ナシ？\",\"結婚対象になる恋人とは？\",\"好きな人に恋人がいたらどうする？\",\"友達と好きな人がかぶったらどうする？\",\"恋人に求めるもの\",\"恋人の条件（こんな人と付き合いたい）\",\"過去最高の褒め言葉\",\"ハメを外してやってみたいこと\",\"理想のプロポーズ \",\" 落ちてるお金いくらまでなら拾う？\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'),'\
    '(\"002\", \"デート\", \"実は知らないパートナーの一面が見れるかも\", \"009\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"お互いの口癖を教え合う\",\"お互いの好きな服\",\"こんな服を着てほしい\",\"今頑張っていること\",\"最近の悩み\",\"お気に入りの写真\",\"お互いの第一印象\",\"印象が変わった所\",\"一番楽しかったデートの思い出\",\"好きな色\",\"お互いを動物に例えるなら\",\"お互いを色に例えるなら\",\"最近見た夢\",\"今週末の予定\",\"こんな習い事してました\",\"お互いの家族の話\",\"自分の人生のピークはいつだと思う？\",\"家で一人の時何をする？\",\"オススメのアプリ\",\"何か一つだけ無人島に持っていくなら\",\"一億円あったらどう使う?\",\"一ヶ月の休暇があったらどう使う？\",\"明日死ぬなら何をする？\",\"小さい頃の夢\",\"過去一番高額な買い物\",\"昔からの宝物\",\"何歳まで生きたい？\",\"付き合ってからの日数を秒に直してみよう\",\"好きになったきっかけ\",\"お互いの好きなところ\",\"今だから言えるぶっちゃけ話\",\"告白のシチュエーションを振り返ろう\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"002\", \"忘年会\", \"一年を振り返る話題がたくさん\", \"010\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"今年やり残したこと\",\"来年の抱負\",\"今年一番の思い出\",\"今年一番の収穫物\",\"クリスマスは何する/何した？\",\"今年一度も使わなかった物・服\",\"今年の抱負は達成できた？\",\"私の年越しの祝い方\",\"今年初めてやったこと\",\"今年一番の失敗\",\"今年一番お金を使ったこと\",\"今年を漢字一文字で表すなら\",\"来年このメンバーで何をする？\",\"今年のテーマソング\",\"今年のベストショット（写真）\",\"今年お世話になった人\",\"年が変わる前にお互いの本音を告白！\",\"今年いちばん印象に残っているニュース\",\"オススメのアプリ\",\"印象が変わった人\",\"今年一番一緒にいた人\",\"直したい癖・習慣\",\"今年一番の褒め言葉\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"003\", \"暇つぶし話題30選\", Null, \"011\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"何か一つだけ無人島に持っていくなら\",\"一億円あったらどう使う?\",\"一ヶ月の休暇があったらどう使う？\",\"明日死ぬなら何をする？\",\"今着ている服の購入背景\",\"今朝起きて最初にしたこと\",\"最近見た夢\",\"今週末の予定\",\"オススメのレストラン\",\"電車の中ってどう過ごす？\",\"自分の地元をPR!\",\"最近のお気に入り写真\",\"動物に生まれ変わるなら何になりたい？\",\"ケータイのホーム画面公開！\",\"ラインの友達何人いる？\",\"小学校あるある\",\"抜き打ち！お互いの誕生日覚えてるかチェック\",\"子供につけたい名前\",\"1日の内SNSにどれくらい時間使う？\",\"最高のご飯のお供\",\"過去一番高額な買い物\",\"理想の旅行プラン\",\"何歳まで生きたい？\",\"怖い話\",\"すべらない話\",\"マイブーム\",\"オススメのアプリ\",\"こういう人が許せない\",\"一年前の今頃何してた？\",\"お互いの良い所を一つずつ言う\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"003\", \"初対面話題決定版\", Null, \"012\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"自分の性格を一言で\",\"今までつけられたあだ名\",\"最近ハッピーだったこと\",\"家族構成\",\"実家の独自文化\",\"恋人はいる？\",\"仕事/バイトは何かしてる？\",\"出身地をPR!\",\"誕生日\",\"マイブーム\",\"趣味\",\"特技\",\"苦手なもの\",\"休日の過ごし方\",\"生活の中のこだわり\",\"こんな癖があります\",\"自分を動物に例えるなら\",\"今住んでる所\",\"今週末の予定\",\"お酒は飲む？\",\"好きな芸能人\",\"好きな食べ物\",\"好きな音楽\",\"これについてなら語れる\",\"好きな季節\",\"好きなスポーツ？\",\"過去最高の褒め言葉\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"003\", \"地味に知らないこんな一面\", Null, \"013\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"起きて最初にすること\",\"お互いの第一印象\",\"恋人の前ではどう振る舞っている？\",\"自分なりのゲンかつぎ\",\"小さい頃の夢\",\"最近読んだ本\",\"こんな習い事してました\",\"電車の中ってどう過ごす？\",\"得意料理\",\"好きな色\",\"自分の人生のピークはいつだと思う？\",\"行ってみたい所\",\"将来の夢\",\"家族の話\",\"至福のひと時\",\"お互いを色で例えるならどんな色？\",\"お酒の失敗エピソード\",\"ハメを外してやってみたいこと\",\"ファッションのこだわり\",\"最高のご飯のお供\",\"昔からの宝物\",\"これに弱い\",\"好きなコンビニ\",\"携帯と財布以外の必需品\",\"過去一番高額な買い物\",\"ケータイのホーム画面公開！\",\"自分なりのリフレッシュ法\",\"この頃に戻りたい\",\"私のお金の使い道・使い方\",\"家で一人の時何をする？\",\"ラインの友達何人いる？\",\"１日の内SNSにどれくらい時間使う？\",\"抜き打ち！お互いの誕生日覚えてるかチェック\",\"お互いの癖\",\"お互いの周りからの評価\",\"お互いのどこが一番好き？\",\"相手の長所短所\",\"過去最高の褒め言葉\",\"今だから言えるぶっちゃけ話\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"003\", \"究極の２択\", Null, \"014\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"稼げる嫌いな仕事 or 稼げない好きな仕事\",\"年中夏 or 年中冬\",\"未来が見れる or 過去が見れる（現実と同じ）\",\"嫌われ者の富豪 or 人気者の貧乏人\",\"色がない世界 or 音のない世界\",\"自分だけブサイク or 自分以外全員ブサイク\",\"付き合うなら好みの 顔 or 性格\",\"明日死ぬ or 不老不死\",\"まずいもの死ぬまで食べる or 好きなもの１日一食だけ\",\"全宇宙の理りを悟る or 全て忘れる\",\"スポーツの才能 or 芸術の才能\",\"壁がない家 or 屋根がない家\",\"時間にルーズな恋人 or お金にルーズな恋人\",\"下手なパイロットの運転 or 上手い素人の運転\",\"夜しか生きられない or 昼しか生きられない\",\"死ぬ年齢を知る vs 死に方を知る\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\'), '\
    '(\"003\", \"面接で問われる話題集\", Null, \"015\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"自己PR\",\"自分の長所・短所\",\"座右の銘\",\"私のこだわり\",\"趣味、特技\",\"他人に負けないこと\",\"大学でなにを学んだか\",\"学業で頑張ったこと、学業以外で頑張ったこと\",\"学生時代一番楽しかったこと・辛かったこと\",\"人生１番の挫折\",\"〇〇業界を志望する理由\",\"将来の夢\",\"１０年後、どうなっていたい？\")), \'2023-06-22 00:00:00\', \'2023-06-22 00:00:00\')'
    await async_client.dbsession.execute(text(sqlstr))
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    
    # ケース１ デフォルトテーマを取得
    response = await async_client.client.get("/browse/retrieve/theme")
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 15 #テーマは全部で15個
    # 見本として”一般”のテーマについて各カラムを確認
    assert response_obj[0]["theme_id"] == 1
    assert response_obj[0]["theme_type"] == "001"
    assert response_obj[0]["title"] == "一般"
    assert response_obj[0]["description"] == "困った時はこれ！"
    assert response_obj[0]["image_type"] == "001"
    assert response_obj[0]["topic"] == {"topic" : ["落ち着く空間","秋といえば？","趣味","今会いたい人","オススメのレストラン","こんな癖があります","特技","ハメを外してやってみたいこと","好きなスポーツ","これについてなら語れる！","好きな映画","家ではどんな格好？","好きなコンビニ","生まれ変わるなら男？女？","一日だけ異性になれるなら何する？","オススメの音楽","オススメのアプリ","最高のご飯のお供","自分の地元をPR!","最近のお気に入り写真","私服のこだわり","遊びでよく行くエリア","得意なモノマネ","苦手なもの","マイブーム","理想の旅行プラン","一ヶ月の休暇があるならどう使う？","一億円あったらどう使う？","私のお金の使い道・使い方","好きな匂い","ケータイのホーム画面公開！","睡眠のこだわり","休日の過ごし方","朝方？夜型？","健康のために心がけていること","好きな場所","至福のひと時","昔からの宝物","実家の独自文化","得意料理","好きなものは先食べる派？","電車の中ってどう過ごす？","こういう人が許せない","好きなブランド","犬派？猫派？","自分を動物に例えるなら","最近ハッピーだったこと","最近見た夢","起きて最初にすること","カラオケの十八番","風邪の自分なりの治療法","自分なりのゲンかつぎ","もし一つだけ魔法がつかえるなら","無人島に一つだけ持っていくなら","一日に鏡を見る回数","今週末の予定","生活の中のこだわり","携帯と財布以外の必需品","行ってみたい国","好きな芸能人","好きな季節","髪を染めたことはある？","好きな時代に行けるなら","一年前の今頃何してた？","家で一人の時何をする？","歌詞を覚えている曲は？","私って何の人で認識されてますか？","過去最高の褒め言葉"," 落ちてるお金いくらまでなら拾う？"]}
    # discriptionがないパターンも確認
    assert response_obj[10]["theme_id"] == 11
    assert response_obj[10]["title"] == "暇つぶし話題30選"
    assert response_obj[10]["description"] == None

    # ケース2 デフォルトテーマの最終更新日時を取得
    response = await async_client.client.get("/browse/retrieve/last-updated-date") 
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 1
    assert response_obj["updated_at"] == "2023-06-22T00:00:00"
    
    # ケース3 新規テーマを追加し、再度最終更新日時を取得
    sqlstr = \
    'INSERT INTO '\
    'prepared_theme(theme_type, title, `description`, image_type, topic, created_at, updated_at) '\
    'VALUES '\
    '(\"004\", \"追加テストテーマ\", \"テストです\", \"888\", JSON_OBJECT(\"topic\", JSON_ARRAY(\"テスト話題1\",\"テスト話題2\",\"テスト話題3\")), \'2023-06-24 00:00:00\', \'2023-06-24 00:00:00\')'
    await async_client.dbsession.execute(text(sqlstr))
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # DBでレコードが更新されていることを確認
    themeRecord = await async_client.dbsession.get(theme_model.PreparedTheme, 16)
    assert themeRecord.image_type == '888'
    assert themeRecord.updated_at == datetime.datetime(2023, 6, 24, 0, 0)
    await async_client.dbsession.close()
    # 他のレコードの更新日時は更新されていないことを確認
    themeRecord = await async_client.dbsession.get(theme_model.PreparedTheme, 1)
    assert themeRecord.updated_at == datetime.datetime(2023, 6, 22, 0, 0)
    await async_client.dbsession.close()
    # 最終更新日時が更新されていることを確認
    response = await async_client.client.get("/browse/retrieve/last-updated-date") 
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 1
    assert response_obj["updated_at"] == "2023-06-24T00:00:00"

    # ケース4 既存テーマに変更を加え、再度最終更新日時を取得
    sqlstr = \
    'UPDATE '\
    'prepared_theme '\
    'SET '\
    'image_type = \'999\', '\
    'updated_at = \'2023-06-24 00:30:00\' '\
    'WHERE '\
    'theme_id = 8 '
    await async_client.dbsession.execute(text(sqlstr))
    await async_client.dbsession.commit()
    await async_client.dbsession.close()

    # DBでレコードが更新されていることを確認
    themeRecord = await async_client.dbsession.get(theme_model.PreparedTheme, 8)
    assert themeRecord.image_type == '999'
    assert themeRecord.created_at != None \
            and themeRecord.updated_at != None \
            and (themeRecord.created_at < themeRecord.updated_at) \
            and (themeRecord.updated_at == datetime.datetime(2023, 6, 24, 0, 30))
    await async_client.dbsession.close()
    # 他のレコードの更新日時は更新されていないことを確認
    themeRecord = await async_client.dbsession.get(theme_model.PreparedTheme, 1)
    assert themeRecord.updated_at == datetime.datetime(2023, 6, 22, 0, 0)
    await async_client.dbsession.close()
    # 最終更新日時が更新されていることを確認
    response = await async_client.client.get("/browse/retrieve/last-updated-date") 
    assert response.status_code == starlette.status.HTTP_200_OK
    response_obj = response.json()
    assert len(response_obj) == 1
    assert response_obj["updated_at"] == "2023-06-24T00:30:00"

#################################################################################################
#############################公開マイリスト取得のテスト#########################################################
#################################################################################################

# 【正常系】全ての公開マイリストを取得
@pytest.mark.asyncio
async def test_retrieve_all_public_mylists(async_client):
    
    # ケース１ デフォルトテーマを取得
    # response = await async_client.client.get("/discover/retrieve/all/")
    # assert response.status_code == starlette.status.HTTP_200_OK
    # response_obj = response.json()
    # assert len(response_obj) == 15 #テーマは全部で15個
    # # 見本として”一般”のテーマについて各カラムを確認
    # assert response_obj[0]["theme_id"] == 1
    # assert response_obj[0]["theme_type"] == "001"
    # assert response_obj[0]["title"] == "一般"
    # assert response_obj[0]["description"] == "困った時はこれ！"
    # assert response_obj[0]["image_type"] == "001"
    # assert response_obj[0]["topic"] == {"topic" : ["落ち着く空間","秋といえば？","趣味","今会いたい人","オススメのレストラン","こんな癖があります","特技","ハメを外してやってみたいこと","好きなスポーツ","これについてなら語れる！","好きな映画","家ではどんな格好？","好きなコンビニ","生まれ変わるなら男？女？","一日だけ異性になれるなら何する？","オススメの音楽","オススメのアプリ","最高のご飯のお供","自分の地元をPR!","最近のお気に入り写真","私服のこだわり","遊びでよく行くエリア","得意なモノマネ","苦手なもの","マイブーム","理想の旅行プラン","一ヶ月の休暇があるならどう使う？","一億円あったらどう使う？","私のお金の使い道・使い方","好きな匂い","ケータイのホーム画面公開！","睡眠のこだわり","休日の過ごし方","朝方？夜型？","健康のために心がけていること","好きな場所","至福のひと時","昔からの宝物","実家の独自文化","得意料理","好きなものは先食べる派？","電車の中ってどう過ごす？","こういう人が許せない","好きなブランド","犬派？猫派？","自分を動物に例えるなら","最近ハッピーだったこと","最近見た夢","起きて最初にすること","カラオケの十八番","風邪の自分なりの治療法","自分なりのゲンかつぎ","もし一つだけ魔法がつかえるなら","無人島に一つだけ持っていくなら","一日に鏡を見る回数","今週末の予定","生活の中のこだわり","携帯と財布以外の必需品","行ってみたい国","好きな芸能人","好きな季節","髪を染めたことはある？","好きな時代に行けるなら","一年前の今頃何してた？","家で一人の時何をする？","歌詞を覚えている曲は？","私って何の人で認識されてますか？","過去最高の褒め言葉"," 落ちてるお金いくらまでなら拾う？"]}
    # # discriptionがないパターンも確認
    # assert response_obj[10]["theme_id"] == 11
    # assert response_obj[10]["title"] == "暇つぶし話題30選"
    # assert response_obj[10]["description"] == None