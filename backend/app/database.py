# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

# pool_pre_ping avoids "server closed the connection" errors on idle connections,
# common with hosted Postgres (Supabase/Neon) after periods of inactivity.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Usage in a router (e.g. routers/orders.py):
# from fastapi import Depends
# from sqlalchemy.orm import Session
# from app.database import get_db

# @router.post("/api/create-order")
# def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
#     ...