import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# pool_pre_ping=True to keep long-lived connections healthy (Neon friendly)
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # ✅ critical so objects don't expire after commit()
    bind=engine,
    future=True,
)

Base = declarative_base()
