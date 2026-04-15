from sqlalchemy import Column, Integer, String, Text, DateTime 
from sqlalchemy.sql import func
from app.database import Base



class QaHistory(Base):
    __tablename__ = "qa_history"
    id=Column(Integer, primary_key=True, index=True)
    question = Column(Text)
    answer = Column(Text)
    chunks_used = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())