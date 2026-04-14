import time
from sqlalchemy.orm import Session
from app.services.embeddings import generate_embedding
from app.database import SessionLocal
from app.models.document_chunks import DocumentChunk
from groq import Groq
from app.env import settings

client =Groq(api_key=settings.GROQ_API_KEY)


def generate_message(prompt:str):
    start_time=time.time()
    response=client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[{"role": "user", "content": prompt}]
    )
    end_time=time.time()
    print("LLM Resaponse Time : ",end_time-start_time)
    return response.choices[0].message.content


def ask_question(query:str,db:Session,top_k=2):
    query_embedding=generate_embedding(query)
    chunks_with_distance = db.query(DocumentChunk, DocumentChunk.embedding.cosine_distance(query_embedding).label('distance')).order_by(DocumentChunk.embedding.cosine_distance(query_embedding)).limit(top_k).all()
    chunks = [chunk for chunk, _ in chunks_with_distance]
    distances = [distance for _, distance in chunks_with_distance]
    best_score = distances[0] if distances else 1.0
    if best_score > 0.4:  # Adjust threshold as needed, smaller distance is better
        return "Sorry, I don't have enough information to answer that question."
    context="\n".join([chunk.chunk_text for chunk in chunks])
    prompt=f"Context: {context}\n\nQuestion: {query}\nAnswer:"
    answer=generate_message(prompt)
    return {
        "answer": answer,
        "source_chunks":[chunk.chunk_text for chunk in chunks]
    } 