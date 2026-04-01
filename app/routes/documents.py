from fastapi import APIRouter, Depends, UploadFile,HTTPException,File
import os
import shutil

from requests import Session
from sqlalchemy import text, func
from app.database import SessionLocal, get_db
from app.services.text_extractor import (
    extract_text_from_pdf,
    chunks_text,
    extract_text_from_docx,
    extract_text_from_txt
    )
from app.models.document import Document
from app.models.document_chunks import DocumentChunk
from app.services.embeddings import generate_embedding_batch

router = APIRouter()
 
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/")
def upload_document(file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        filename=file.filename
        ext=filename.split(".")[-1].lower()
        if ext not in ["pdf","docx","txt"]:
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, and TXT are allowed.")
        
        file_path=os.path.join(UPLOAD_DIR,filename)
        with open(file_path,"wb") as buffer:
            shutil.copyfileobj(file.file,buffer)

        if ext=="pdf":
            text=extract_text_from_pdf(file_path)
        elif ext=="docx":
            text=extract_text_from_docx(file_path)  
        else:
            text=extract_text_from_txt(file_path)
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text found in file.")
        
        chunks=chunks_text(text)

        embeddings=generate_embedding_batch(chunks)

        document=Document(
            title=filename,
            content=text,
            file_type=ext,
            search_vector=func.to_tsvector('english', text)
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        for i,chunk in enumerate(chunks):
            chunk_obj=DocumentChunk(
                document_id=document.id,
                chunk_text=chunk,
                chunk_index=i,
                embedding=embeddings[i]
            )
            db.add(chunk_obj)
        db.commit()
        return {"message":"File uploaded and processed successfully.",
                "document_id":document.id,
                "total_chunks":len(chunks)
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:        
        db.close()



@router.get("/")
def get_documents(skip:int=0,limit:int=10,db:Session=Depends(get_db)):
    documents=db.query(Document).offset(skip).limit(limit).all()
    return documents


@router.get("/{document_id}")
def get_document(document_id:int,db:Session=Depends(get_db)):
    document=db.query(Document).filter(Document.id==document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{id}/chunks")
def get_document_chunks(id:int,db:Session=Depends(get_db)):
    chunks=db.query(DocumentChunk).filter(DocumentChunk.document_id==id).all()
    if not chunks:
        raise HTTPException(status_code=404, detail="Document chunks not found")
    return [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "text": chunk.chunk_text,
            "chunk_index": chunk.chunk_index,
            # "embedding": chunk.embedding
        } 
        for chunk in chunks
    ]






@router.get("/{id}/similar")
def similar_documents(id:int,db:Session=Depends(get_db)):
    avg_embedding_query=text("""
        SELECT AVG(embedding) as avg_embedding
        FROM document_chunks
        WHERE document_id = :doc_id
    """)
    result=db.execute(avg_embedding_query,{"doc_id":id}).fetchone()
    if not result or not result.avg_embedding:
        raise HTTPException(status_code=404, detail="Document or embedding not found")
    avg_embedding=result.avg_embedding
    similarity_query=text("""
        SELECT d.id, d.title, d.content, 
        (SELECT AVG((embedding <-> :avg_embedding)) FROM document_chunks WHERE document_id = d.id) as similarity
        FROM documents d
        WHERE d.id != :doc_id
        ORDER BY similarity ASC
        LIMIT 5
    """)
    results=db.execute(similarity_query,{
        "avg_embedding":avg_embedding,
        "doc_id":id}).fetchall()
    return [
        {
            "document_id": row.id,
            "title": row.title,
            "similarity": float(row.similarity)
        }
        for row in results
    ]



@router.delete("/{document_id}")
def delete_document(document_id:int,db:Session=Depends(get_db)):
    document=db.query(Document).filter(Document.id==document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(document)
    db.commit()
    return {"message":"Document deleted successfully."}



@router.put("/{document_id}")
def update_document(document_id:int, content:str=None, db:Session=Depends(get_db)):
    document=db.query(Document).filter(Document.id==document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    document.content=content
    chunks=chunks_text(content)
    embeddings=generate_embedding_batch(chunks)
    db.query(DocumentChunk).filter(DocumentChunk.document_id==document_id).delete()
    for i,chunk in enumerate(chunks):
        chunk_obj=DocumentChunk(
            document_id=document.id,
            chunk_text=chunk,
            chunk_index=i,
            embedding=embeddings[i]
        )
        db.add(chunk_obj)
    db.commit()
    return {"message":"Document updated successfully."}