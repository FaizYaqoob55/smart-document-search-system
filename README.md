# smart-document-search-system

# Overview

This project is an AI-powered document search system that allows users to upload documents and search them using both semantic (AI-based) and keyword-based search.

# Features

- Upload documents (PDF, DOCX, TXT)
- Text extraction and chunking
- AI embeddings generation using sentence-transformers
- Semantic search (meaning-based)
- Keyword search (PostgreSQL full-text search)
- Hybrid search (combination of semantic + keyword)
- Similar documents detection
- Search analytics (popular searches, trends)
- Full CRUD operations

# Tech Stack
- FastAPI
- PostgreSQL + pgvector
- SQLAlchemy
- sentence-transformers

# Setup Instructions

1. Clone repo:
```bash
git clone <https://github.com/FaizYaqoob55/smart-document-search-system.git>
cd project