from app.database import get_db
from app.models.document import Document
from app.models.document_chunks import DocumentChunk
from app.models.url_sources import UrlSources
from app.services.create_session_chat import create_session, get_history, save_message, load_session
from fastapi import APIRouter, Depends, HTTPException
from app.services.llm_service import ask_question
from sqlalchemy.orm import Session
import app.database as db
from app.services.llm_service import client
from app.services.create_session_chat import r
from app.services.scrapper_services import ingest_url_pipeline









router = APIRouter()


# @router.post("/document/ingest/url")
# def ingest_url(data: dict, db: Session = Depends(get_db)):
#     url = data["url"]
#     scrapped = scrapped_url(url)
#     content = scrapped["content"]
#     title = scrapped.get("title") or "Untitled"

#     doc = Document(title=title, content=content, source_url=url)
#     db.add(doc)
#     db.commit()
#     db.refresh(doc)

#     chunks = chunks_text(content)
#     embeddings =generate_embeddings_batch(chunks)
#     for i, chunk in enumerate(chunks):
#         chunk_doc = chunk_data.append({"document_id": doc.id, "content": chunk, "chunk_index": i, "embedding": embeddings[i]})
#         db.bulk_insert_mappings(DocumentChunk, chunk_data)
#     db.commit()
#     return {"message": "URL ingested successfully", "document_id": doc.id}



@router.get("/document/ingest/urls")
def get_urls(db: Session = Depends(get_db)):
    urls = db.query(UrlSources).all()
    return {"urls": urls}



# @router.post("/document/ingest/urls/{id}refresh")
# def refresh_url(id: int, db: Session = Depends(get_db)):
#     url_entry = db.query(UrlSources).filter(UrlSources.id == id).first()
#     if not url_entry:
#         raise HTTPException(status_code=404, detail="URL entry not found")
#     scrapped = scrapped_url(url_entry.url)
#     content = scrapped["content"]
#     title = scrapped.get("title") or "Untitled"

#     doc = Document(title=title, content=content, source_url=url_entry.url)
#     db.add(doc)
#     db.commit()
#     db.refresh(doc)

#     chunks = chunks_text(content)
#     embeddings =generate_embeddings_batch(chunks)
#     chunk_data = []
#     for i, chunk in enumerate(chunks):
#         chunk_data.append({"document_id": doc.id, "content": chunk, "chunk_index": i, "embedding": embeddings[i]})
#         db.bulk_insert_mappings(DocumentChunk, chunk_data)
#     db.commit()
#     return {"message": "URL refreshed successfully", "document_id": doc.id}






@router.post("/documents/ingest/url")
def ingest_url(
    data: dict,
    db: Session = Depends(get_db)
):

    url = data["url"]

    title = data.get("title")

    doc = ingest_url_pipeline(
        url,
        db,
        title
    )

    return {
        "message": "URL indexed successfully",
        "document_id": doc.id
    }



@router.post("/documents/ingest/urls")
def ingest_urls(
    data: dict,
    db: Session = Depends(get_db)
):

    urls = data["urls"]

    results = []

    for url in urls:

        doc = ingest_url_pipeline(
            url,
            db
        )

        results.append({
            "url": url,
            "document_id": doc.id
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


