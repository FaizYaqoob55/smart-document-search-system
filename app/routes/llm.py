from app.services.llm_service import ask_question, generate_message
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.qa_history import QaHistory
router = APIRouter()

@router.post("/llm/ask")
def get_llm_message(question: str):
   answer = generate_message(question)
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
      