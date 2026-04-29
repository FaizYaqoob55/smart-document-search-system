from typing import List, Optional

from app.database import get_db
from app.models.document import Document
from app.models.document_chunks import DocumentChunk
from app.models.url_sources import UrlSources
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from app.services.llm_service import ask_question
from sqlalchemy.orm import Session
import app.database as db
from app.services.llm_service import client
from app.services.create_session_chat import r
from app.services.scrapper_services import ingest_url_pipeline


router = APIRouter()


class URLIngestRequest(BaseModel):
    url: HttpUrl
    title: Optional[str] = None


class URLsIngestRequest(BaseModel):
    urls: List[HttpUrl] = Field(alias="url")













@router.get("/document/ingest/urls")
def get_urls(db: Session = Depends(get_db)):
    urls = db.query(UrlSources).all()
    results = []

    for u in urls:
        document = db.query(Document).filter(Document.source_url == u.url).first()
        results.append({
            "urls": u.url,
            "id": u.id,
            "document_id": document.id if document else None,
            "last_scraped_at": u.last_scraped_at,
            "scrape_status": u.scrape_status,
            "next_scrape_at": u.next_scrape_at,
        })

    return results



@router.post("/documents/ingest/url")
def ingest_url(
    data: URLIngestRequest,
    db: Session = Depends(get_db)
):

    url = str(data.url)

    try:
        doc = ingest_url_pipeline(
            url,
            db,
            data.title
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return {
        "message": "URL indexed successfully",
        "document_id": doc.id
    }


@router.post("/documents/ingest/urls")
def ingest_urls(
    data: URLsIngestRequest,
    db: Session = Depends(get_db)
):

    results = []

    for url_obj in data.urls:
        url = str(url_obj)

        try:
            doc = ingest_url_pipeline(
                url,
                db
            )
            results.append({
                "url": url,
                "document_id": doc.id
            })
        except ValueError as exc:
            results.append({
                "url": url,
                "error": str(exc)
            })


    return {
        "message": "Bulk URLs indexed",
        "results": results
    }




@router.post(
    "/documents/sources/urls/{id}/refresh"
)
def refresh_url(
    id: int,
    db: Session = Depends(get_db)
):

    source = db.query(
        UrlSources
    ).filter(
        UrlSources.id == id
    ).first()

    if not source:

        return {
            "error": "URL not found"
        }

    doc = ingest_url_pipeline(
        source.url,
        db
    )

    return {
        "message": "URL refreshed",
        "document_id": doc.id
    }


