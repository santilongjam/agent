import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

load_dotenv()

_raw_url = os.getenv("DATABASE_URL", "")
if not _raw_url:
    raise RuntimeError("DATABASE_URL environment variable is required")

# Render provides postgres:// — SQLAlchemy needs postgresql+psycopg2://
DATABASE_URL = _raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    __import__("app.models.task")          # registers TaskModel
    __import__("app.models.conversation")  # registers ConversationMessage
    __import__("app.models.user")          # registers UserModel
    Base.metadata.create_all(bind=engine)
