import os

from sqlmodel import Session, SQLModel, create_engine


def format_database_url(url: str | None) -> str:
    """Helper to ensure DATABASE_URL is valid for SQLAlchemy"""
    if not url:
        return "sqlite:///./local_dev.db"
    # Heroku provides DATABASE_URL, but imports it with 'postgres://' which SQLAlchemy doesn't like.
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


database_url = format_database_url(os.environ.get("DATABASE_URL"))
engine = create_engine(database_url, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
