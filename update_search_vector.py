from app.database import engine
from sqlalchemy import text

# Update search_vector for existing documents
with engine.connect() as conn:
    conn.execute(text("UPDATE documents SET search_vector = to_tsvector('english', content) WHERE search_vector IS NULL"))
    conn.commit()

print("Updated search_vector for existing documents")