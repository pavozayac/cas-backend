from typing import final
from .database import SessionLocal

def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()