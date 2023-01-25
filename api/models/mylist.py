import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, JSON, DateTime
from api.db import Base

class MyList(Base):
    __tablename__ = "my_list"
    my_list_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    user_id = Column(Integer, ForeignKey('m_user.user_id'), nullable=False) 
    title = Column(String(30))
    theme_type = Column(String(3))
    # topic = Column(String(8500))
    topic = Column(JSON())
    is_private = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=False)


    

    