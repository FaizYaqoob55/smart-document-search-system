import time
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, Float
from app.models.qa_history import QaHistory
from app.services.embeddings import generate_embedding
from app.models.document_chunks import DocumentChunk
from app.models.document import Document
from groq import Groq
from app.env import settings

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




# def generate_message(prompt: str):
#     """LLM se jawab mangwane ka function"""
#     start_time = time.time()
    
#     payload = {
#         "inputs": prompt,
#         "parameters": {
#             "max_new_tokens": 250, 
#             "temperature": 0.3, # Quality ke liye temperature kam rakha hai
#             "return_full_text": False 
#         }
#     }

#     try:
#         response = client.chat.completions.create(
#             model='llama-3.1-8b-instant',
#             messages=[{"role": "user", "content": prompt}]
#         )
#         result = response.choices[0].message.content
        
#         if isinstance(result, str):
#             return result
#         elif isinstance(result, dict) and "error" in result:
#             return f"AI Error: {result.get('error')}"
#         return "Unexpected response format."

#     except Exception as e:
#         return f"Connection Error: {str(e)}"

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

    # 5. Prompt Taiyar Karna
    prompt = f"""Use the following context to answer the question. 
If you don't know, say "I don't know". 
Keep it professional.

Context:
{context}

Question:
{query}

Answer:"""

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