from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


# 全マイリスト取得リクエストパラメータ
class retrieveAllMylistsParam(BaseModel):
    user_id: int

# マイリスト取得レスポンス
class Mylist(BaseModel):
    my_list_id: int
    title: str = Field(..., min_length=1, max_length=30, description="マイリストのタイトル")
    theme_type: str = Field(..., min_length=3, max_length=3, description="マイリストのサムネイルイラストコード") 
    topic: dict = Field(..., description="トピックのリスト") 
    is_private: bool = Field(..., description="非公開フラグ")

    @field_validator("topic")
    def check_topic_format(cls, dictvalue: dict)-> Union[str, ValueError]:
        if dictvalue is None:
            raise ValueError("topic dict should not be None")
        elif 'topic' not in dictvalue:
            raise ValueError("topic dict should have a key with name 'topic'")
        elif type(dictvalue["topic"]) is not list:
            raise ValueError("type of value for topic dict is not list")
        return dictvalue

    model_config = ConfigDict(from_attributes = True)

# 初回マイリスト作成リクエストパラメータ
class createUserThenMylistParam(BaseModel):
    title: str = Field(..., min_length=1, max_length=30, description="マイリストのタイトル")
    theme_type: str = Field(..., min_length=3, max_length=3, description="マイリストのサムネイルイラストコード") 
    topic: Optional[dict] = Field({"topic" : []}, description="トピックのリスト") #topicがない場合は空の配列で保存する
    is_private: Optional[bool] = Field(False, description="非公開フラグ")

    @field_validator("topic")
    def check_topic_format(cls, dictvalue: dict)-> Union[str, ValueError]:
        if dictvalue is None:
            raise ValueError("topic dict should not be None")
        elif 'topic' not in dictvalue:
            raise ValueError("topic dict should have a key with name 'topic'")
        elif type(dictvalue["topic"]) is not list:
            raise ValueError("type of value for topic dict is not list")
        return dictvalue

# マイリスト作成リクエストパラメータ
class createMylistParam(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1, max_length=30, description="マイリストのタイトル")
    theme_type: str = Field(..., min_length=3, max_length=3, description="マイリストのサムネイルイラストコード")
    # topic: Optional[List[str]] = Field(None, min_items=0, max_items=100, description="トピックのリスト") 
    topic: Optional[dict] = Field({"topic" : []}, description="トピックのリスト") #topicがない場合は空の配列で保存する
    is_private: Optional[bool] = Field(False, description="非公開フラグ")

    @field_validator("topic")
    def check_topic_format(cls, dictvalue: dict)-> Union[str, ValueError]:
        if dictvalue is None:
            raise ValueError("topic dict should not be None")
        elif 'topic' not in dictvalue:
            raise ValueError("topic dict should have a key with name 'topic'")
        elif type(dictvalue["topic"]) is not list:
            raise ValueError("type of value for topic dict is not list")
        return dictvalue

#　マイリスト更新リクエストパラメータ
class updateMyListParam(BaseModel):
    my_list_id: int
    title: str = Field(..., min_length=1, max_length=30, description="マイリストのタイトル")
    theme_type: str = Field(..., min_length=3, max_length=3, description="マイリストのサムネイルイラストコード")
    is_private: bool = Field(..., description="非公開フラグ")

#　マイリストタイトル更新リクエストパラメータ
class updateTitleParam(BaseModel):
    title: str = Field(..., min_length=1, max_length=30, description="マイリストのタイトル")

#　マイリストテーマ更新リクエストパラメータ
class updateThemeParam(BaseModel):  
    theme_type: str = Field(..., min_length=3, max_length=3, description="マイリストのサムネイルイラストコード")

# トピック更新リクエストパラメータ
class updateTopicParam(BaseModel):  
    topic: dict = Field(..., description="トピックのリスト")

    @field_validator("topic")
    def check_topic_format(cls, dictvalue: dict)-> Union[str, ValueError]:
        if dictvalue is not None and 'topic' not in dictvalue:
            raise ValueError("topic dict should have a key with name 'topic'")
        elif type(dictvalue["topic"]) is not list:
            raise ValueError("type of value for topic dict is not list")
        return dictvalue

# 非公開フラグ更新リクエストパラメータ
class updatePrivateFlagParam(BaseModel):  
    is_private: bool

# Realmデータからマイリスト作成リクエストパラメータ（リスト）の各要素
class createMylistFromRealmParam(BaseModel):
    title: str = Field(..., min_length=1, max_length=30, description="マイリストのタイトル")
    topic: dict = Field(..., description="トピックのリスト")
    created_at: datetime = Field(..., description="クライアント側での作成日時")

    @field_validator("topic")
    def check_topic_format(cls, dictvalue: dict)-> Union[str, ValueError]:
        if dictvalue is None:
            raise ValueError("topic dict should not be None")
        elif 'topic' not in dictvalue:
            raise ValueError("topic dict should have a key with name 'topic'")
        elif type(dictvalue["topic"]) is not list:
            raise ValueError("type of value for topic dict is not list")
        return dictvalue

# 初回マイリスト作成レスポンス
class createUserThenMylistResponse(Mylist):
    user_id: int

# マイリスト作成レスポンス
class createMylistResponse(Mylist):
    pass

# 通報フラグ更新レスポンス
class updateReportedFlagResponse(Mylist):
    reported_flag: bool


# Realmデータからマイリスト作成レスポンス    
class createMylistFromRealmResponse(BaseModel):
    user_id: int
    mylists: list[Mylist]
    