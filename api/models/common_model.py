# 下記の方法だと最初のcreated_atとupdated_atを完全に同一時刻にできないため、各モデルにそれぞれ登録日時、更新日時を都度定義する方針に変更。

# from zoneinfo import ZoneInfo
# from sqlalchemy import Column, DateTime
# from sqlalchemy.ext.declarative import declared_attr
# from datetime import datetime

# class TimestampMixin(object):
#     now = datetime.utcnow

#     @declared_attr
#     def created_at(cls):
#         return Column(DateTime, default=cls.now, nullable=False)

#     @declared_attr
#     def updated_at(cls):
#         return Column(DateTime, default=cls.now, onupdate=cls.now, nullable=False)