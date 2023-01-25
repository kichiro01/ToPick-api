import datetime
from sqlalchemy import Column, Integer, DateTime
from api.db import Base


class User(Base):
    __tablename__ = "m_user"
    user_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=False)
    