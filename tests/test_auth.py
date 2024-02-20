from datetime import timedelta
import pytest
import starlette.status
from sqlalchemy import select

from api.models import auth_model


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

    # ケース3 異常系_パラメータなし
    response = await async_client.client.post("/auth/create")
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース4 異常系_パラメータのキー名が不正
    response = await async_client.client.post("/auth/create", json={
        "user_idWrong": 1,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース5 異常系_パラメータがNone
    response = await async_client.client.post("/auth/create", json={
        "user_id": None,
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    
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
    
    # ケース9 認証_異常系_パラメータが空
    response = await async_client.client.post("/auth/authenticate", json={})
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース10 認証_異常系_パラメータのキー名が不正_認証ID
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_idWrong": 1,
        "auth_code": codeValue
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース11 認証_異常系_パラメータのキー名が不正_認証コード
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1,
        "auth_codeWrong": codeValue
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース12 認証_異常系_パラメータがNone_認証ID
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": None,
        "auth_code": codeValue
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース13 認証_異常系_パラメータがNone_認証コード
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1,
        "auth_code": None
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

    # ケース14 認証_異常系_パラメータ不足_認証ID
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_code": codeValue
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース15 認証_異常系_パラメータ不足_認証コード
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース16 認証_正常系_認証コードが6桁未満
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1,
        "auth_code": 'abc12'
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ケース17 認証_正常系_認証コードが7桁以上
    response = await async_client.client.post("/auth/authenticate", json={
        "auth_id": 1,
        "auth_code": 'abc1234'
    })
    assert response.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    
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

