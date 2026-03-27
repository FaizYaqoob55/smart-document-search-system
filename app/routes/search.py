from fastapi import APIRouter, Depends, Query
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embeddings import generate_embedding

router = APIRouter()
@router.get("/semantic")
def semantic_search(query: str = Query(...), db: Session = Depends(get_db)):
    query_embedding = generate_embedding(query)
    sql = text("""
               SELECT 
                    dc.id,
                    dc.chunk_text,
                    dc.document_id,
                    dc.chunk_index,
                    1-(dc.embedding <=> CAST(:query_embedding AS vector)) AS similarity
               FROM document_chunks dc
               ORDER BY dc.embedding <=> CAST(:query_embedding AS vector)
               LIMIT 10

    """)
    result = db.execute(sql, {"query_embedding": query_embedding}).fetchall()
    return [{"chunk_id": row.id,
              "document_id": row.document_id,
              "text": row.chunk_text, 
              "chunk_index": row.chunk_index, 
              "similarity": row.similarity
            #   "similarity": f"{row.similarity * 100:.2f}%"
            }  
             for row in result]