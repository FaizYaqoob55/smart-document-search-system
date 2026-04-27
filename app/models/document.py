from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSVECTOR
from app.database import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    title= Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    file_type = Column(String, nullable=True)
    search_vector = Column(TSVECTOR, nullable=True)
    source_url = Column(String, nullable=True)
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete")





