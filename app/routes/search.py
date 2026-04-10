from fastapi import APIRouter, Depends, Query, HTTPException
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models.search_history import SearchHistory
from app.models.document import Document
from app.services.embeddings import generate_embedding
from datetime import datetime

router = APIRouter()

@router.get("/semantic")
def semantic_search(query: str, file_type: str = Query(None), date_from: str = Query(None), date_to: str = Query(None), db: Session = Depends(get_db)):
    query_embedding = generate_embedding(query)

    filters = []
    parms = {"query_embedding": query_embedding}
    if file_type:
        filters.append("d.file_type = :file_type")
        parms["file_type"] = file_type.lower()
    if date_from:
        try:
            # Assume YYYY-MM-DD format
            parsed_date = datetime.strptime(date_from, "%Y-%m-%d")
            filters.append("d.created_at >= :date_from")
            parms["date_from"] = parsed_date
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD.")
    if date_to:
        try:
            parsed_date = datetime.strptime(date_to, "%Y-%m-%d")
            filters.append("d.created_at <= :date_to")
            parms["date_to"] = parsed_date
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD.")
    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)
    sql = text(f"""
               SELECT 
                    dc.id,
                    dc.chunk_text,
                    dc.chunk_index,
                    dc.document_id,
                    1 - (dc.embedding <=> (:query_embedding)::vector) AS similarity 
               FROM document_chunks dc
               JOIN documents d ON dc.document_id = d.id
               {where_clause}
               ORDER BY dc.embedding <=> (:query_embedding)::vector
               LIMIT 10
    """)
    result = db.execute(sql, parms).fetchall()
    db.add(SearchHistory(
        query=query,
        search_type="semantic",
        results_count=len(result)
    ))
    db.commit()

    return [{"chunk_id": row.id,
              "document_id": row.document_id,
              "text": row.chunk_text, 
              "chunk_index": row.chunk_index, 
              "similarity": row.similarity
            #   "similarity": f"{row.similarity * 100:.2f}%"
            }  
             for row in result]

    
@router.get("/keyword")
def keyword_search(query: str, db: Session = Depends(get_db)):
    results=db.query(Document.id, Document.title, func.ts_rank(
        Document.search_vector, func.plainto_tsquery(query)).label("score")).filter(
    
    Document.search_vector.op("@@")(func.plainto_tsquery(query))
    ).order_by(func.ts_rank(Document.search_vector, func.plainto_tsquery(query)).desc()).limit(10).all()

    #log the search query and results count
    search_history=SearchHistory(
        query=query,
        search_type="keyword", 
        results_count=len(results)
    )
    db.add(search_history)
    db.commit()
    return [{"document_id": row.id, "title": row.title, "score": float(row.score)} for row in results]




@router.get("/hybrid")
def hybrid_search(query: str,db: Session = Depends(get_db)):
    query_embedding = generate_embedding(query)
    semantic_results = db.execute(text("""
    SELECT 
        d.id, 
        1 - (dc.embedding <=> (:query_embedding)::vector) AS similarity
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    ORDER BY dc.embedding <=> (:query_embedding)::vector
    LIMIT 10
"""), {"query_embedding": query_embedding}).fetchall()
    keyword_results=db.query(Document.id, func.ts_rank(
        Document.search_vector, func.plainto_tsquery(query)).label("score")).filter(
    
    Document.search_vector.op("@@")(func.plainto_tsquery(query))
    ).order_by(func.ts_rank(Document.search_vector, func.plainto_tsquery(query)).desc()).limit(10).all()

    #combine and rank results
    combined_results={}
    for row in semantic_results:
        combined_results[row.id]={"semantic_score": row.similarity, "keyword_score": 0}
    for row in keyword_results:
        if row.id in combined_results:
            combined_results[row.id]["keyword_score"]=row.score
        else:
            combined_results[row.id]={"semantic_score": 0, "keyword_score": row.score}
    ranked_results=sorted(combined_results.items(), key=lambda x: x[1]["semantic_score"] + x[1]["keyword_score"], reverse=True)[:10]

    return [{"document_id": doc_id, "semantic_score": scores["semantic_score"], "keyword_score": scores["keyword_score"]} for doc_id, scores in ranked_results]



