# Load environment variables before anything else
from dotenv import load_dotenv
load_dotenv()

import os

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Transaction, Token
from app.database import SessionLocal, engine, get_db

from datetime import datetime

from typing import Optional
from pydantic import BaseModel

class TokenCreate(BaseModel):
    token: str
    is_stable: bool

class TransactionCreate(BaseModel):
    timestamp: str
    from_token: str
    to_token: str
    from_amount: float
    to_amount: float

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

def format_datetime_for_input(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d %H:%M:%S')

templates.env.filters['datetimeformat'] = format_datetime_for_input


GIT_COMMIT = (
    os.getenv("RENDER_GIT_COMMIT")
    or os.getenv("GIT_COMMIT")
    or "unknown"
)

# Home page - Show transactions
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    return templates.TemplateResponse(request, "index.html", {"request": request, "git_commit": GIT_COMMIT, "transactions": transactions})

# Add transaction form
@app.get("/add", response_class=HTMLResponse)
async def add_transaction_page(request: Request):
    return templates.TemplateResponse(request, "add_transaction.html", {"request": request, "git_commit": GIT_COMMIT, "now": datetime.utcnow()})

# Handle transaction submission
@app.post("/add", response_class=JSONResponse)
async def add_transaction(timestamp: datetime = Form(...), amount: float = Form(...), token: str = Form(...), total_usd: float = Form(...), db: Session = Depends(get_db)):
    try:
        new_transaction = Transaction(timestamp=timestamp, amount=amount, token=token, total_usd=total_usd)
        db.add(new_transaction)
        db.commit()
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            content={"error": f"Transaction with timestamp '{timestamp}' and token '{token}' already exists"},
            status_code=409,
        )
    return {"status": "success", "message": f"Transaction with timestamp '{timestamp}', and {amount} {token}, and USD {total_usd} added"}

# Token management endpoints
@app.post("/tokens", response_class=JSONResponse)
async def add_token(token_data: TokenCreate, db: Session = Depends(get_db)):
    token = token_data.token
    is_stable = token_data.is_stable
    
    # Check if token already exists with a different stability setting
    existing_token = db.query(Token).filter(Token.name == token).first()
    if existing_token:
        if existing_token.is_stable != is_stable:
            stability_type = "stablecoin" if existing_token.is_stable else "non-stablecoin"
            return JSONResponse(
                content={"error": f"'{token}' is already marked as a {stability_type}."},
                status_code=409,
            )
        return {"status": "success", "message": f"Token '{token}' already exists"}
    
    # Add the new token
    new_token = Token(name=token, is_stable=is_stable)
    db.add(new_token)
    db.commit()
    return {"status": "success", "message": f"Token '{token}' marked as {'stablecoin' if is_stable else 'non-stablecoin'}"}

@app.get("/tokens/{token_name}", response_class=JSONResponse)
async def get_token(token_name: str, db: Session = Depends(get_db)):
    token = db.query(Token).filter(Token.name == token_name).first()
    if not token:
        return JSONResponse(
            content={"error": f"Token '{token_name}' not found"},
            status_code=404,
        )
    return {"name": token.name, "is_stable": token.is_stable}

