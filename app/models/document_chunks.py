from sqlalchemy import Column, Float, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from pgvector.sqlalchemy import Vector


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(384))
    ocr_confidence = Column(Float, nullable=True)
    image_path = Column(String, nullable=True)

    document = relationship("Document", back_populates="chunks")
