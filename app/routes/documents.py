from fastapi import APIRouter, Depends, UploadFile, HTTPException, File
import os
import shutil
from sqlalchemy.orm import Session
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
import threading

router = APIRouter()
 
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

import time 
# --- BACKGROUND WORKER ---
def process_full_document_background(doc_id: int, file_path: str, ext: str):
    """Heavy processing: Extraction -> Chunking -> Embeddings"""
    db = SessionLocal() # Naya session for background thread
    try:
         # 1. Text Extraction (Wait thora sa taake file write complete ho)
        time.sleep(1) 
        if ext == "pdf":
            text = extract_text_from_pdf(file_path)
        elif ext == "docx":
            text = extract_text_from_docx(file_path)
        else:
            text = extract_text_from_txt(file_path)

        if not text or not text.strip():
            print(f"✗ Error: Document {doc_id} extracted text is empty.")
            return

        # 2. Document Table Update (Original Text & Search Vector)
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.content = text
            doc.search_vector = func.to_tsvector('english', text)
            db.commit()

        # 3. Chunking & Embeddings
        # Recommendation: 15MB file ke liye chunk_size 1500-2000 rakhein
        chunks = chunks_text(text)
        embeddings = generate_embedding_batch(chunks)

        # 4. Bulk Save Chunks (Fastest Way)
        chunk_data = [
            {
                "document_id": doc_id,
                "chunk_text": c,
                "chunk_index": i,
                "embedding": embeddings[i],
            }
            for i, c in enumerate(chunks)
        ]

        # Direct dictionary list bhejain, objects banane ki zaroorat nahi
        db.bulk_insert_mappings(DocumentChunk, chunk_data)
        db.commit()


        
        print(f"✅ Background Success: Document {doc_id} processed ({len(chunks)} chunks).")

    except Exception as e:
        print(f"✗ Background Critical Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

# --- UPLOAD ROUTE ---        
#    async  mean  doing multiple tasks without blocking the system 
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SECRET_KEY") # Use Secret Key for backend
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@router.post("/upload/")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        filename = file.filename
        ext = filename.split(".")[-1].lower()
        
        if ext not in ["pdf", "docx", "txt"]:
            raise HTTPException(status_code=400, detail="Only PDF, DOCX, TXT allowed.")

        # 1. Read file content for Supabase
        file_content = await file.read()
        
        # 2. Upload to Supabase Storage (Bucket name: 'document')
        # Path format: 'filename' or 'folder/filename'
        storage_path = f"{int(time.time())}_{filename}" # Unique name taake override na ho
        
        try:
            supabase.storage.from_('document').upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": file.content_type}
            )
            # Public URL hasil karein (Optional, agar DB mein save karna ho)
            file_url = supabase.storage.from_('document').get_public_url(storage_path)
        except Exception as storage_err:
            print(f"❌ Supabase Storage Error: {str(storage_err)}")
            # Agar storage fail ho tab bhi hum local process jari rakh sakte hain ya error de sakte hain
        
        # 3. Local Copy (Background worker ke liye asaan hai)
        file_path = os.path.abspath(os.path.join(UPLOAD_DIR, filename))
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        # 4. Database Entry
        new_doc = Document(
            title=filename,
            file_type=ext,
            content="Processing...", 
            # file_url=file_url # Agar aapne model mein field banayi hai
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        # 5. Start Background Thread
        thread = threading.Thread(
            target=process_full_document_background,
            args=(new_doc.id, file_path, ext),
            daemon=True
        )
        thread.start()

        return {
            "message": "✓ Uploaded to Supabase & Local! AI processing started.",
            "document_id": new_doc.id,
            "supabase_url": file_url if 'file_url' in locals() else None
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Upload Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")




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


@router.get("/{document_id}/status")
def get_embedding_status(document_id: int, db: Session = Depends(get_db)):
    """Check if embeddings are done processing for uploaded document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()
    
    return {
        "document_id": document_id,
        "title": document.title,
        "chunks_processed": chunk_count,
        "status": "embeddings_ready" if chunk_count > 0 else "processing"
    }


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






# @router.get("/{id}/similar")
# def similar_documents(id:int,db:Session=Depends(get_db)):
#     avg_embedding_query=text("""
#         SELECT AVG(embedding) as avg_embedding
#         FROM document_chunks
#         WHERE document_id = :doc_id
#     """)
#     result=db.execute(avg_embedding_query,{"doc_id":id}).fetchone()
#     if not result or not result.avg_embedding:
#         raise HTTPException(status_code=404, detail="Document or embedding not found")
#     avg_embedding=result.avg_embedding
#     similarity_query=text("""
#         SELECT d.id, d.title, d.content, 
#         COALESCE((SELECT AVG((embedding <-> :avg_embedding)) FROM document_chunks WHERE document_id = d.id), 0) as similarity
#         FROM documents d
#         WHERE d.id != :doc_id
#         ORDER BY similarity ASC
#         LIMIT 5
#     """)
#     results=db.execute(similarity_query,{
#         "avg_embedding":avg_embedding,
#         "doc_id":id}).fetchall()
#     return [
#         {
#             "document_id": row.id,
#             "title": row.title,
#             "similarity": float(row.similarity) if row.similarity is not None else 0.0
#         }
#         for row in results
#     ]



@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    # 1. Check karein ke document exist karta hai ya nahi
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # 2. Pehle saare Chunks delete karein (Zarori Step)
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()

        # 3. Phir main Document delete karein
        db.delete(document)
        
        db.commit()
        return {"message": f"Document ID {document_id} deleted successfully."}
    
    except Exception as e:
        db.rollback()
        print(f"Error during deletion: {str(e)}")

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




# @router.put("/{document_id}")
# def update_document(document_id:int, content:str=None, db:Session=Depends(get_db) ):
#     document=db.query(Document).filter(Document.id==document_id).first()
#     if not document:
#         raise HTTPException(status_code=404,detail="Document not found")
#     document.content=content
#     document.search_vector=func.to_tsvector('english',content)
#     chunks=chunks_text(content)
#     embedding=generate_embedding_batch(chunks)
#     db.query(Document).filter(Document.id==document_id).update({
#         "content":content,
#         "search_vector":func.to_tsvector('english',content)
#     })
#     db.query(DocumentChunk).filter(DocumentChunk.document_id==document_id).delete()
#     db.commit() 
#     return {"Message":"Document update successfully"}
