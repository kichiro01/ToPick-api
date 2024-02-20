
from fastapi.exceptions import ResponseValidationError
import pytest
import starlette.status

from api.models import mylist_model
from api.cruds import mylist_cruds


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
async def test_mylist_user_create_irreqular(async_client):
    # ケース１ theme_typeなしで作成
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース１_2 theme_typeをNoneで作成
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "ユーザーなし作成テスト",
        "theme_type": None
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース2 titleなしで作成
    response = await async_client.client.post("/mylist/create-user", json={
        "theme_type": "002"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース2_2 titleをNoneで作成
    response = await async_client.client.post("/mylist/create-user", json={
        "title": None,
        "theme_type": "002"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース3 topicの形式が不正（topicsになっている）
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topics" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース4 topicの形式が不正（空の辞書）
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース5 topicがNone
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": None,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース6 topicの辞書のvalueの型が不正
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : "配列ではない"},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース7 topicの辞書のvalueの型が不正(None)
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : None},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    

# 【異常系】マイリスト追加
@pytest.mark.asyncio
async def test_mylist_create_irregular(async_client):
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
    
    # ケース2_2 user_idをNoneで作成
    response = await async_client.client.post("/mylist/create", json={
        "user_id": None,
        "title": "ユーザーなし作成テスト",
        "theme_type": "001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース3 theme_typeなしで作成
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "ユーザーなし作成テスト"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース3_2 theme_typeをNoneで作成
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "ユーザーなし作成テスト",
        "theme_type": None
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース4 titleなしで作成
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "theme_type": "002"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース4_2 titleをNoneで作成
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": None,
        "theme_type": "002"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース5 topicの形式が不正（topicsになっている）
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topics" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース6 topicの形式が不正（空の辞書）
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース7 topicがNone
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": None,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース8 topicの辞書のvalueの型が不正
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : "配列ではない"},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース9 topicの辞書のvalueの型が不正(None)
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "002",
        "topic": {"topic" : None},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    
# 【境界値】マイリスト作成（ユーザー作成）
@pytest.mark.asyncio
async def test_mylist_user_create_border(async_client):  
    # ケース1 titleが1文字未満
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "",
        "theme_type": "001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

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

    # ケース5 theme_typeが2文字
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "01"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース6 theme_typeが4文字
    response = await async_client.client.post("/mylist/create-user", json={
        "title": "123456789012345678901234567890",
        "theme_type": "0001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

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

    # ケース5 theme_typeが2文字
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "01"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース6 theme_typeが4文字
    response = await async_client.client.post("/mylist/create", json={
        "user_id": 1,
        "title": "123456789012345678901234567890",
        "theme_type": "0001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    

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

    # ケース4 異常系_パラメータなし
    response = await async_client.client.put("/mylist/title/1")
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース5 異常系_パラメータのキー名が不正
    response = await async_client.client.put("/mylist/title/1", json={
        "titleWrong": "test",
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース6 異常系_パラメータがNone
    response = await async_client.client.put("/mylist/title/1", json={
        "title": None
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース7 境界値_１文字未満
    response = await async_client.client.put("/mylist/title/1", json={
        "title": ""
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース8 境界値_31文字
    response = await async_client.client.put("/mylist/title/1", json={
        "title": "1234567890123456789012345678901"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
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

    # ケース4 異常系_パラメータなし
    response = await async_client.client.put("/mylist/theme/1")
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース5 異常系_パラメータのキー名が不正
    response = await async_client.client.put("/mylist/theme/1", json={
        "theme_typeWrong": "001",
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース6 異常系_パラメータがNone
    response = await async_client.client.put("/mylist/theme/1", json={
        "theme_type": None
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース7 境界値_3文字未満
    response = await async_client.client.put("/mylist/theme/1", json={
        "theme_type": "01"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース8 境界値_4文字
    response = await async_client.client.put("/mylist/theme/1", json={
        "theme_type": "0001"
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
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

    # ケース4 異常系_パラメータなし
    response = await async_client.client.put("/mylist/topic/1")
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース5 異常系_パラメータのキー名が不正
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic_typeWrong": {"topic" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース6 異常系_パラメータがNone
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": None,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース7 異常系_topicの形式が不正（topicsになっている）
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": {"topics" : ["話題１", "話題２", "話題３"]},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース8 異常系_topicの形式が不正（空の辞書）
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": {},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース9 topicの辞書のvalueの型が不正
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": {"topic" : "配列ではない"},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース10 topicの辞書のvalueの型が不正(None)
    response = await async_client.client.put("/mylist/topic/1", json={
        "topic": {"topic" : None},
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

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

    # ケース4 異常系_パラメータなし
    response = await async_client.client.put("/mylist/privateflag/1")
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース5 異常系_パラメータのキー名が不正
    response = await async_client.client.put("/mylist/privateflag/1", json={
        "is_privateWrong": True,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース6 異常系_パラメータがNone
    response = await async_client.client.put("/mylist/privateflag/1", json={
        "is_private": None,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
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
    response = await async_client.client.delete("/mylist/1")
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Mylist with id 1 not found"
    }

# 異常系_全マイリスト取得
@pytest.mark.asyncio
async def test_mylist_retrieve_validation(async_client):
    # test_mylist_user_createのケース7,8で存在しないユーザーへの取得、
    # test_mylist_deleteのケース3で存在するユーザーのマイリストが0件の場合のテストは実施済
    # ⇨このシナリオでは、DBを直にいじって不正なデータを作り、マイリスト取得時の各項目のバリデーションのテスト(想定するエラーが発生するかどうか)を行う。
    
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
    original = await mylist_cruds.getMylistById(async_client.dbsession, mylist_id=1)
    original.title = ""
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    # ケース2_title文字数上限違反
    # タイトルを入れ直す
    original.title = "1234567890123456789012345678901"
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    # ケース3_titleがNone
    original.title = None
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

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
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")
    
    # ケース5 theme_type上限違反
    original.theme_type = "0001"
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    # ケース6 theme_typeがNone
    original.theme_type = None
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

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
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")
    
    # ケース8 topicの形式が不正（空の辞書）
    original.topic = {}
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")
    
    # ケース9 topicがNone
    original.topic = None
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    # ケース10 topicの辞書のvalueの型が不正
    original.topic = {"topic" : "配列ではない"}
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

    # ケース11 topicの辞書のvalueの型が不正(None)
    original.topic = {"topic" : None}
    async_client.dbsession.add(original)
    await async_client.dbsession.commit()
    await async_client.dbsession.close()
    # API呼び出し
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")

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
    with pytest.raises(ResponseValidationError) as e:
        await async_client.client.get("/mylist/retrieve/all/1")
