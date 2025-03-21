# Load environment variables before anything else
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.models import Base, Transaction
from app.database import SessionLocal, engine, get_db

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Home page - Show transactions
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    return templates.TemplateResponse(request, "index.html", {"request": request, "transactions": transactions})

# Add transaction form
@app.get("/add", response_class=HTMLResponse)
async def add_transaction_page(request: Request):
    return templates.TemplateResponse(request, "add_transaction.html", {"request": request})

# Handle transaction submission
@app.post("/add", response_class=HTMLResponse)
async def add_transaction(amount: float = Form(...), token: str = Form(...), db: Session = Depends(get_db)):
    new_transaction = Transaction(amount=amount, token=token)
    db.add(new_transaction)
    db.commit()
    return f'<tr><td>{amount}</td><td>{token}</td></tr>'  # HTMX replaces content dynamically
