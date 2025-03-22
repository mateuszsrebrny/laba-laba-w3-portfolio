from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, Float, String
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    token = Column(String(8), nullable=False)


