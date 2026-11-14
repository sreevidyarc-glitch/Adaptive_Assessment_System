import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("adaptive_assessment.database")

Base = declarative_base()

def get_engine():
    db_url = settings.DATABASE_URL
    # Render and Heroku use postgres:// which SQLAlchemy requires as postgresql+psycopg2://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgresql://") and "+psycopg2" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    try:
        if db_url.startswith("postgresql"):
            # Attempt to connect to PostgreSQL with a short timeout
            engine = create_engine(
                db_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 3}
            )
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected successfully to PostgreSQL database.")
            return engine
        else:
            engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
            )
            return engine
    except Exception as exc:
        logger.warning(
            f"Could not connect to configured database at '{db_url}': {exc}. "
            f"Falling back to local SQLite database at '{settings.FALLBACK_SQLITE_URL}' for development."
        )
        return create_engine(
            settings.FALLBACK_SQLITE_URL,
            connect_args={"check_same_thread": False}
        )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models import user, course, question, assessment  # noqa
    Base.metadata.create_all(bind=engine)

