from app.services.llm_service import generate_message
from fastapi import APIRouter
router = APIRouter()

@router.post("/llm/ask")
def get_llm_message(question: str):
   answer = generate_message(question)
   return {
      "question": question,
      "answer": answer
      }
