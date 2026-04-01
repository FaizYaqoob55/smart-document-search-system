from fastapi import FastAPI
from app.routes import analytics, documents, search
app = FastAPI(title="Smart Document Search System")

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Document Search System!"}