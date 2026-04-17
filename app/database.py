from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker
from .env import settings

SQLALCHEMY_DATABASE_URL = "postgresql://neondb_owner:npg_K5VyCJxl1wUm@ep-flat-pond-am9x3f6y-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
# engine = create_engine(settings.DATABASE_URL, echo=True, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except OperationalError as e:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database connection failed. Check DATABASE_URL and network access. "
                f"Original error: {e}"
            ),
        )
    finally:
        try:
            db.close()
        except Exception as e:
            # Log the error but don't propagate to avoid breaking the response
            print(f"Error closing database session: {e}")
            pass