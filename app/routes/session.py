import json
import uuid
from app.database import get_db
from app.services.create_session_chat import create_session, get_history, save_message, load_session
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


@router.get("/chat/sessions/{session_id}/history")
def get_chat_history(session_id: str):
    history = get_history(session_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"history": history}
  




@router.delete("/chat/sessions/{session_id}")
def delete_chat_session(session_id: str):
    r.delete(f"session:{session_id}")
    return {"detail": "Session deleted"}





@router.get("/chat/sessions")
def list_chat_sessions():
    keys = r.keys("session:*")
    sessions = [key.split(":")[1] for key in keys]
    return {"sessions": sessions}



@router.post("/chat/sessions/{session_id}/message")
def chat(session_id: str, query: str, db: Session = Depends(get_db)):

    session_data = load_session(session_id)
    if session_data is None:
        return {"error": "Invalid session"}

    history = get_history(session_id)
    document_ids = session_data.get("document_ids", []) if isinstance(session_data, dict) else []

    # :fire: RAG with document scope
    rag_result = ask_question(query, db, document_id=document_ids)

    context = rag_result["answer"]

    # :fire: build messages
    messages = history + [
        {"role": "user", "content": query},
        {"role": "system", "content": context}
    ]

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )

    answer = response.choices[0].message.content
    save_message(session_id, "user", query)
    save_message(session_id, "assistant", answer)

    return {
        "answer": answer,
        "citations": rag_result.get("citations", []),
        "session_id": session_id
    }





@router.post("/chat/sessions/{session_id}/new-topic")
def new_topic(session_id: str):
    raw = r.get(f"session:{session_id}")
    if not raw:
        return {"error": "Invalid session"}

    data = json.loads(raw)
    if isinstance(data, list):
        data = {"history": []}
    else:
        data["history"] = []

    r.set(f"session:{session_id}", json.dumps(data), ex=86400)

    return {"message": "Context cleared"}



from fastapi.responses import Response

@router.get("/chat/sessions/{session_id}/export")
def export_chat(session_id: str):
    raw = r.get(f"session:{session_id}")
    if not raw:
        return {"error": "Invalid session"}

    data = json.loads(raw)
    history = data["history"]

    text = ""
    for msg in history:
        text += f"{msg['role']}: {msg['content']}\n\n"

    return Response(
        content=text,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=chat_{session_id}.txt"
        }
    )


