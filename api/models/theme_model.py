import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime
from api.db import Base

class PreparedTheme(Base):
    __tablename__ = "prepared_theme"
    theme_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    theme_type = Column(String(3), nullable=False)
    title = Column(String(30), nullable=False)
    description = Column(String(50))
    image_type = Column(String(3), nullable=False)
    topic = Column(JSON(), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=False)