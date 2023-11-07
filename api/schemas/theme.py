from datetime import datetime
from typing import List, Optional, Union
from xmlrpc.client import boolean
from pydantic import BaseModel, Field, validator

# デフォルトテーマ取得レスポンス
class PreparedTheme(BaseModel):
    theme_id: int
    theme_type: str = Field(..., min_length=3, max_length=3, description="テーマ種別コード") 
    title: str = Field(..., min_length=1, max_length=30, description="テーマのタイトル")
    description: Optional[str] = Field(..., max_length=50, description="テーマの説明文")
    image_type: str = Field(..., min_length=3, max_length=3, description="テーマのサムネイル画像コード")
    topic: dict = Field(..., description="トピックのリスト")
    
    @validator("topic")
    def check_topic_format(cls, dictvalue: dict)-> Union[str, ValueError]:
        if dictvalue is None:
            raise ValueError("topic dict should not be None")
        elif 'topic' not in dictvalue:
            raise ValueError("topic dict should have a key with name 'topic'")
        elif type(dictvalue["topic"]) is not list:
            raise ValueError("type of value for topic dict is not list")
        return dictvalue

    class Config:
        orm_mode = True

# 最終更新日取得レスポンス
class LastUpdatedDate(BaseModel):
    updated_at: datetime = Field(..., description="最終更新日時")

    class Config:
        orm_mode = True