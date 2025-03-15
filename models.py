from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
from sqlalchemy import Column, Integer, Float, String

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    token = Column(String, nullable=False)

# Create tables
Base.metadata.create_all(bind=engine)

# Helper function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
