# Load environment variables before anything else
from dotenv import load_dotenv
load_dotenv()

import os

from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Transaction
from app.database import SessionLocal, engine, get_db

from datetime import datetime

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
async def add_transaction(timestamp: datetime = Form(...), amount: float = Form(...), token: str = Form(...), db: Session = Depends(get_db)):
    try:
    	new_transaction = Transaction(timestamp=timestamp, amount=amount, token=token)
    	db.add(new_transaction)
    	db.commit()
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            content={"error": f"Transaction with timestamp '{timestamp}' and token '{token}' already exists"},
            status_code=409,
        )
    return {"status": "success", "message": f"Transaction with timestamp '{timestamp}', and {amount} {token} added"}
