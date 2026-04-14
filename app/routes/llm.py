from app.services.llm_service import ask_question, generate_message
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
router = APIRouter()

@router.post("/llm/ask")
def get_llm_message(question: str):
   answer = generate_message(question)
   return {
      "question": question,
      "answer": answer
      }


@router.post("/rag/ask")
def rag_ask(question:str, db: Session = Depends(get_db), document_id:int=None):
   return ask_question(question, db)