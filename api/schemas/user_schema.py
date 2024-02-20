from pydantic import BaseModel, ConfigDict

# 新規ユーザー作成レスポンス
class createUserResponse(BaseModel):
    user_id: int

    model_config = ConfigDict(from_attributes = True)