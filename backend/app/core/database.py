"""SQLAlchemy database engine, session, and Base model."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
engine_kwargs = {
    "echo": settings.DEBUG,
}

if "sqlite" in db_url:
    connect_args["check_same_thread"] = False
else:
    # Neon Serverless Postgres & Cloud Postgres optimizations:
    # pool_pre_ping checks that connection is alive before issuing SQL (vital for Neon scale-to-zero wakeups)
    # pool_recycle cleans up stale TCP connections every 5 minutes
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
