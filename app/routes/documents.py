from fastapi import APIRouter, UploadFile,HTTPException,File
import os
import shutil
from app.database import SessionLocal
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
            file_type=ext
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










