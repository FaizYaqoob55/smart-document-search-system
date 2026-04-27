from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy import func
from app.database import Base


class UrlSources(Base):
    __tablename__ = "url_sources"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True,nullable=False)
    last_scraped_at = Column(DateTime)
    scrape_status=Column(String)
    next_scrape_at = Column(DateTime)