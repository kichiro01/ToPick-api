from datetime import timedelta
from pydantic import ValidationError
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import starlette.status
from sqlalchemy import select

from api.db import get_db, Base
from api.main import app

import api.models.mylist as mylist_model
import api.models.auth as auth_model
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