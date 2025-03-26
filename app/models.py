from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, Float, String, DateTime
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    token = Column(String(8), nullable=False)
    amount = Column(Float, nullable=False)


