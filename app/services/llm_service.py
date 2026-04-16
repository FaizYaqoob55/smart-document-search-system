import time
from sqlalchemy.orm import Session
from sqlalchemy import func, Float
from app.models.qa_history import QaHistory
from app.services.embeddings import generate_embedding
from app.models.document_chunks import DocumentChunk
from app.models.document import Document
from groq import Groq
from app.env import settings
from app.services.prompt_templates import factual_prompt, summary_prompt, comparison_prompt

client = Groq(api_key=settings.GROQ_API_KEY)


def generate_message(prompt: str):
    start_time = time.time()
    response = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[{"role": "user", "content": prompt}]
    )
    end_time = time.time()
    print("LLM Response Time :", end_time - start_time)
    return response.choices[0].message.content

def stream_response(prompt: str):
    stream = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content




def detect_query_type(query: str):
    query = query.lower()

    if "compare" in query or "difference" in query:
        return "comparison"

    elif "summarize" in query or "summary" in query:
        return "summary"

    else:
        return "factual"




def ask_question(query: str, db: Session, top_k: int = 2, document_id: int = None):
    """Database se search karke AI jawab dene ka main function"""
    start_time = time.time()

    # 1. Sawal ko Embedding mein badalna
    # Note: ensure generate_embedding function is imported
    query_embedding = generate_embedding(query)

    # 2. Database Search (Cosines Distance use karte hue)
    # <=> operator PGVector mein distance ke liye hota hai
    query_db = db.query(
        DocumentChunk,
        Document.title,
        DocumentChunk.embedding.op("<=>", return_type=Float)(query_embedding).label("score")
    ).join(Document, Document.id == DocumentChunk.document_id)

    # Agar specific document mein search karna ho
    if document_id:
        query_db = query_db.filter(DocumentChunk.document_id == document_id)

    # Top 5 results uthayein filter karne ke liye
    raw_results = query_db.order_by("score").limit(5).all()

    if not raw_results:
        return {"answer": "I don't have any documents to search from.", "citations": []}

    # 3. Filtering aur Deduplication (Duplicated text hatana)
    seen = set()
    final_results = []

    for r in raw_results:
        chunk_obj = r[0]
        doc_title = r[1]
        score = r[2]
        
        similarity = 1 - score # Distance ko similarity mein badla

        if similarity < 0.3: # Threshold check
            continue

        text = chunk_obj.chunk_text.strip()
        if text not in seen:
            seen.add(text)
            final_results.append({
                "chunk": chunk_obj,
                "title": doc_title,
                "similarity": similarity
            })

    if not final_results:
        return {"answer": "Sorry, I couldn't find relevant info in documents.", "citations": []}

    # User ki demand ke mutabiq results limit karein (top_k)
    final_results = final_results[:top_k]

    # 4. Context Saaf Karna
    context_list = []
    for i, res in enumerate(final_results):
        clean_text = res["chunk"].chunk_text.strip().replace("\n", " ")
        context_list.append(f"[Doc{i+1}]: {clean_text}")
    
    context = "\n\n".join(context_list)

    query_type = detect_query_type(query)

    if query_type == "comparison":
        prompt = comparison_prompt(context, query)

    elif query_type == "summary":
        prompt = summary_prompt(context, query)

    else:
        prompt = factual_prompt(context, query)

    answer = generate_message(prompt)

    # 6. Citations (References) banana
    citations = []
    for i, res in enumerate(final_results):
        citations.append({
            "ref": f"Doc{i+1}",
            "doc_title": res["title"],
            "score": round(res["similarity"], 3),
            "snippet": res["chunk"].chunk_text[:150] + "..."
        })

    # 7. History Save Karna (Optional but good)
    qa = QaHistory(
         question=query,
         answer=answer,
         chunks_used=str(citations)
    )
    db.add(qa)
    db.commit()

    end_time = time.time()

    return {
        "answer": answer,
        "citations": citations,
        "response_time": f"{round(end_time - start_time, 2)}s"
    }