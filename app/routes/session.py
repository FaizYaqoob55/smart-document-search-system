from  app.services.create_session_chat import create_session, get_history, save_message
from fastapi import APIRouter, Depends, HTTPException
from app.services.llm_service import ask_question
from sqlalchemy.orm import Session
import app.database as db
from app.services.llm_service import client
from app.services.create_session_chat import r

router = APIRouter()


@router.post("/chat/session")
def create_chat_session():
    session_id = create_session()
    return {"session_id": session_id}


@router.post("/chat/sessions/{session_id}/message")
def chat(session_id: str, query: str, db: Session = Depends(db.get_db)):

    # 1. load history
    history = get_history(session_id)

    # 2. RAG context (reuse your function)
    rag_result = ask_question(query, db)

    context = rag_result["answer"]

    # 3. build messages
    messages = history + [
        {"role": "user", "content": query},
        {"role": "system", "content": context}
    ]

    # 4. LLM call
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )

    answer = response.choices[0].message.content

    # 5. save to redis
    save_message(session_id, "user", query)
    save_message(session_id, "assistant", answer)

    return {
        "answer": answer,
        "session_id": session_id,
        "message_count": len(history) + 2,
        "citations": rag_result.get("citations", [])
    }


