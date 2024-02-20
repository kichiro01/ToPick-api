import datetime
from xmlrpc.client import Boolean
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from api.db import Base

class Auth(Base):
    __tablename__ = "auth"
    auth_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    user_id = Column(Integer, ForeignKey('m_user.user_id'), nullable=False) 
    auth_code = Column(String(6))
    is_authenticated = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=False)