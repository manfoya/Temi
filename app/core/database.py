# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Pour le dev, on reste sur SQLite.
# En production, on changera juste cette ligne pour PostgreSQL.
SQLALCHEMY_DATABASE_URL = "sqlite:///./temi.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dépendance pour récupérer la DB dans les endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
