from __future__ import annotations

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()


def build_database_url() -> str:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB")

    missing_vars = []

    if not user:
        missing_vars.append("POSTGRES_USER")
    if not password:
        missing_vars.append("POSTGRES_PASSWORD")
    if not database:
        missing_vars.append("POSTGRES_DB")

    if missing_vars:
        raise RuntimeError(
            f"Missing required database environment variables: {', '.join(missing_vars)}"
        )

    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


DATABASE_URL = build_database_url()

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def create_db_session() -> Session:
    return SessionLocal()
