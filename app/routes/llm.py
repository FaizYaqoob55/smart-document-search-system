from dns import query

from app.services.embeddings import generate_embedding
from app.services.llm_service import ask_question, detect_query_type, generate_message, stream_response
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.qa_history import QaHistory
from app.services.prompt_templates import comparison_prompt, factual_prompt, summary_prompt
from app.models.document_chunks import DocumentChunk
from app.models.document import Document
from sqlalchemy import Float
router = APIRouter()

@router.post("/llm/ask")
def get_llm_message(question: str):
   query_type = detect_query_type(query)

   if query_type == "comparison":
       prompt = comparison_prompt(query)

   elif query_type == "summary":
       prompt = summary_prompt(query)

   else:
       prompt = factual_prompt(query)
    
   answer = generate_message(prompt)
   return {
      "question": question,
      "answer": answer
      }


@router.post("/rag/ask")
def rag_ask(question:str,document_id:int=None, db: Session = Depends(get_db)):
   return ask_question(question, db,document_id=document_id)


@router.get("/qa_history/{question_id}")
def get_qa_history(question_id: int, db: Session = Depends(get_db)):
      return db.query(QaHistory).filter(QaHistory.id == question_id).first()





from fastapi.responses import StreamingResponse

# @router.get("/rag/ask/stream")
# async def stream_rag(query: str, db: Session = Depends(get_db)):
#     try:
#         # Retrieve context using existing ask_question logic (adjust if needed)
#         rag_result = ask_question(query, db)
#         context = rag_result.get("context", "")  # Assuming ask_question returns a dict with 'context'
        
#         if not context:
#             raise HTTPException(status_code=404, detail="No relevant documents found")
        
#         query_type = detect_query_type(query)
        
#         if query_type == "comparison":
#             prompt = comparison_prompt(context, query)
#         elif query_type == "summary":
#             prompt = summary_prompt(context, query)
#         else:
#             prompt = factual_prompt(context, query)
        
#         return StreamingResponse(
#             stream_response(prompt),
#             media_type="text/plain"
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")
      






@router.get("/rag/ask/stream")
def stream_rag(query: str, db: Session = Depends(get_db)):

    # :fire: STEP 1: SAME RAG RETRIEVAL
    query_embedding = generate_embedding(query)

    results = db.query(
        DocumentChunk,
        Document.title,
        DocumentChunk.embedding.op("<=>", return_type=Float)(query_embedding).label("score")
    ).join(Document, Document.id == DocumentChunk.document_id) \
     .order_by("score").limit(3).all()

    if not results:
        return {"error": "No relevant document found"}

    # :fire: STEP 2: context build
    context = "\n\n".join([
        r[0].chunk_text.strip().replace("\n", " ")
        for r in results
    ])

    # :fire: STEP 3: prompt select
    query_type = detect_query_type(query)

    if query_type == "comparison":
        prompt = comparison_prompt(context, query)
    elif query_type == "summary":
        prompt = summary_prompt(context, query)
    else:
        prompt = factual_prompt(context, query)

    # :fire: STEP 4: streaming response
    return StreamingResponse(
        stream_response(prompt),
        media_type="text/plain"
    )