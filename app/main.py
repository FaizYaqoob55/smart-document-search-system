from fastapi import FastAPI
from starlette.formparsers import MultiPartParser
import uvicorn
from contextlib import asynccontextmanager

# Increase multipart upload limits so file uploads larger than 1MB work correctly.
# Starlette defaults to 1MB per part, which was causing multipart parse failures.
MultiPartParser.spool_max_size = 50 * 1024 * 1024
orig_multipart_init = MultiPartParser.__init__

def multipart_parser_init(self, headers, stream, *, max_files=1000, max_fields=1000, max_part_size=50 * 1024 * 1024):
    orig_multipart_init(self, headers, stream, max_files=max_files, max_fields=max_fields, max_part_size=max_part_size)

MultiPartParser.__init__ = multipart_parser_init

from app.routes import analytics, documents, search,llm, session,url_ingest
from app.services.scrapper_services import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(title="Smart Document Search System", lifespan=lifespan)

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(llm.router,prefix="/llm",tags=["LLM"]) 
app.include_router(session.router, prefix="/session", tags=["Session"])
app.include_router(url_ingest.router, prefix="/url-ingest", tags=["URL Ingest"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Document Search System!"}


if __name__ == "__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)