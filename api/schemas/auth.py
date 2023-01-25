from typing import List, Optional
from pydantic import BaseModel, Field

# 認証コード発行リクエストパラメータ
class createAuthCodeParam(BaseModel):
    user_id: int

# 認証コード発行　レスポンス
class Auth(BaseModel):
    auth_id: int
    auth_code: str = Field(..., min_length=6, max_length=6, description="認証コード")

    class Config:
        orm_mode = True

# 認証リクエストパラメータ
class authenticateParam(Auth):
    pass

# 認証レスポンス
class authenticateResponse(BaseModel):
    user_id: int