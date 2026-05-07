# Smart Document Search System - 5-Minute Demo Script

This script provides a step-by-step walkthrough to demonstrate the core features of the Smart Document Search System in under 5 minutes.

## Setup Before the Demo
1. Ensure the backend is running (`uvicorn app.main:app --reload`).
2. Ensure Redis is running (for chat sessions).
3. Have a sample scanned invoice (Image/PDF) ready.
4. Have the URL of a recent BBC article ready (e.g., a short news piece).
5. Have Swagger UI open in the browser (`http://localhost:8000/docs`).

---

## Part 1: Image OCR & Data Extraction (1.5 Mins)

**Objective:** Show that the system can read non-searchable images/scans and answer questions about them.

1. **Upload the Invoice:**
   - Go to `POST /documents/upload/image`.
   - Upload the sample scanned invoice.
   - *Talk Track:* "We start by uploading a scanned image or invoice. The system automatically detects it's an image and runs Tesseract OCR to extract the text, chunks it, and creates embeddings."
2. **Ask a Question:**
   - Go to `POST /llm/rag/ask`.
   - Set `question` to: *"What is the total amount on the invoice?"*
   - Set `document_id` to the ID returned from the upload step.
   - *Talk Track:* "Now, using our RAG endpoint, we ask the AI a specific question about the document we just uploaded. The AI retrieves the relevant chunk using vector search and generates the precise answer based strictly on the OCR text."

---

## Part 2: Web Scraping & URL Ingestion (1.5 Mins)

**Objective:** Show how easily the system can ingest live web content.

1. **Ingest a URL:**
   - Go to `POST /documents/ingest/url`.
   - Provide the BBC article URL in the request body.
   - *Talk Track:* "Next, let's say we found a useful article online and want to add it to our knowledge base. We just pass the URL. The system scrapes the main content, strips out the noise, and embeds it into the database instantly."
2. **Summarize the Article:**
   - Go to `POST /llm/rag/ask`.
   - Set `question` to: *"What are the key points of this article?"*
   - Set `document_id` to the newly created document ID.
   - *Talk Track:* "Now we can ask our LLM to summarize the article. Because our prompt engineering detects a 'summary' intent, it formats the output cleanly as key takeaways."

---

## Part 3: Chat Sessions & Conversational Memory (2 Mins)

**Objective:** Demonstrate that the system remembers the context of an ongoing conversation.

1. **Start a Session:**
   - Go to `POST /session/chat/session` to create a new session. Copy the `session_id`.
   - *Talk Track:* "For a more interactive experience, we can start a chat session. This creates a persistent session backed by Redis."
2. **First Question:**
   - Go to `POST /session/chat/sessions/{session_id}/message`.
   - Set `query` to: *"What is the main topic of the BBC article we just ingested?"*
   - *Talk Track:* "We ask an initial question. The system searches our vector database, injects the context, and answers."
3. **Follow-up Question 1:**
   - Send another message: *"Can you give me more details about that?"*
   - *Talk Track:* "Notice I said 'that' without specifying the topic. The AI remembers the context from the previous turn and elaborates correctly."
4. **Follow-up Question 2:**
   - Send another message: *"How does it compare to the invoice we uploaded earlier?"*
   - *Talk Track:* "Here, we ask it to draw a comparison. The system retains the chat history and fetches additional context if needed to form a coherent response."
5. **Show Memory State (Optional):**
   - Go to `GET /session/chat/sessions/{session_id}/history` to show the stored message array.
   - *Talk Track:* "Behind the scenes, the full context is maintained in Redis, ensuring fast and stateful LLM interactions."

---
*End of Demo.*
