from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base


class Advertisement(Base):
    __tablename__ = "advertisements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    author = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)