from pydantic import BaseModel

# 新規ユーザー作成レスポンス
class createUserResponse(BaseModel):
    user_id: int

    class Config:
        orm_mode = True