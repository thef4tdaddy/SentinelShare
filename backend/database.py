from sqlmodel import SQLModel, create_engine, Session
import os

# Heroku provides DATABASE_URL, but imports it with 'postgres://' which SQLAlchemy doesn't like.
# We need to replace it with 'postgresql://'
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Fallback for local development
if not database_url:
    database_url = "sqlite:///./local_dev.db"

engine = create_engine(database_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
