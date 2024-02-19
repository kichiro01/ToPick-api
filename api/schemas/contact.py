from pydantic import BaseModel, Field

# 意見・要望投稿リクエストパラメータ
class contactRequestParam(BaseModel):
    user_id: int
    text: str = Field(..., min_length=1, max_length=100, description="意見・要望の投稿内容")

# 通報リクエストパラメータ
class reoprtRequestParam(BaseModel):
    user_id: int
    reported_mylist_id: int
    reason_code: str = Field(..., min_length=3, max_length=3, description="通報理由コード")
    report_content: str = Field(..., min_length=1, max_length=100, description="通報内容詳細")
