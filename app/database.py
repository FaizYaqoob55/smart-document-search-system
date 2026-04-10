from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .env import settings

# SQLALCHEMY_DATABASE_URL = "postgresql://neondb_owner:npg_K5VyCJxl1wUm@ep-flat-pond-am9x3f6y-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
engine = create_engine(settings.DATABASE_URL,echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()