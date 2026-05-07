# Prompt Engineering Guidelines

This document outlines the prompt templates used in the Smart Document Search System and the rationale behind their design. The system dynamically selects prompts based on the detected intent of the user's query (Factual, Comparison, or Summary).

## 1. Factual Prompt
Used for direct questions requiring specific information from the documents.

**Template:**
```text
You are a highly intelligent and precise AI assistant. 
Answer the user's question based strictly on the provided context below.
Do not use outside knowledge. If the answer is not in the context, say: "I couldn't find the answer in the provided documents."

Context:
{context}

Question: {question}
```

**Why it works:**
- **Role definition:** "highly intelligent and precise AI assistant" sets a professional tone.
- **Strict Constraints:** "strictly on the provided context" minimizes hallucination (making up facts).
- **Fallback Rule:** Providing a specific phrase ("I couldn't find the answer...") prevents the LLM from guessing when it lacks information.

---

## 2. Comparison Prompt
Used when the user asks to compare two concepts, documents, or data points.

**Template:**
```text
You are an analytical AI assistant.
Compare the entities or concepts mentioned in the user's question based strictly on the provided context.
Highlight similarities and differences clearly, preferably using bullet points.

Context:
{context}

Question: {question}
```

**Why it works:**
- **Role definition:** "analytical AI assistant" encourages structured, logical output.
- **Formatting Constraint:** "preferably using bullet points" ensures the response is easy to scan and digest, which is essential for comparisons.
- **Targeted Action:** Explicitly asks to "Highlight similarities and differences".

---

## 3. Summary Prompt
Used when the user asks for a summary, overview, or "key points" of a document or topic.

**Template:**
```text
You are an expert summarizer.
Provide a concise and comprehensive summary of the provided context related to the user's question.
Focus on the key takeaways and main arguments. Use bullet points for readability.

Context:
{context}

Question: {question}
```

**Why it works:**
- **Role definition:** "expert summarizer" tunes the LLM to extract the most important information rather than getting bogged down in details.
- **Focus:** "key takeaways and main arguments" directs the model to filter noise.
- **Formatting:** "Use bullet points for readability" creates a clean, structured output.

---

## 4. Chat Memory (Session RAG) Prompt
For chat sessions, the system needs to retain conversational context while also referencing retrieved documents.

**Dynamic Construction:**
In chat sessions, the retrieved document context is injected as a `system` message immediately following the conversation history and preceding the latest user query.

**Why it works:**
- By placing the retrieved RAG context *closest* to the user's latest query as a system message, the LLM pays the most attention to it (due to recency bias in Transformer models).
- The earlier messages (history) provide the conversational state, allowing the LLM to resolve pronouns (e.g., "What did you mean by *it*?") correctly before consulting the context.
