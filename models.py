from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .db import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(512), nullable=False)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    decisions = Column(Text, nullable=True)  # JSON string
    action_items = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


