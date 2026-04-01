from fastapi import APIRouter, Depends
from requests import Session
from sqlalchemy import func
from app.database import  get_db
from app.models.search_history import SearchHistory

router = APIRouter()

@router.get("/popular-searches/")
def popular_searches(db: Session = Depends(get_db)):
    history = db.query(SearchHistory.__table__.c.query, func.count(SearchHistory.id).label("count")
                        ).group_by(SearchHistory.__table__.c.query).order_by(func.count(SearchHistory.id).desc()).limit(10).all()
    return [{"query": row[0], "count": row[1]} for row in history]

@router.get("/search-trends/")
def search_trends(db: Session = Depends(get_db)):
    history = db.query(func.date_trunc('day', SearchHistory.created_at).label("date"),
                        func.count(SearchHistory.id).label("count")
                        ).group_by(func.date_trunc('day', SearchHistory.created_at)).order_by(func.date_trunc('day', SearchHistory.created_at).desc()).limit(30).all()
    return [{"date": row[0], "count": row[1]} for row in history]