from fastapi import FastAPI
from app.routes import documents, search
app = FastAPI(title="Smart Document Search System")

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(search.router, prefix="/search", tags=["Search"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Document Search System!"}