from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from models import Transaction, get_db

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Home page - Show transactions
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    return templates.TemplateResponse("index.html", {"request": request, "transactions": transactions})

# Add transaction form
@app.get("/add", response_class=HTMLResponse)
async def add_transaction_page(request: Request):
    return templates.TemplateResponse("add_transaction.html", {"request": request})

# Handle transaction submission
@app.post("/add", response_class=HTMLResponse)
async def add_transaction(amount: float = Form(...), token: str = Form(...), db: Session = Depends(get_db)):
    new_transaction = Transaction(amount=amount, token=token)
    db.add(new_transaction)
    db.commit()
    return f'<tr><td>{amount}</td><td>{token}</td></tr>'  # HTMX replaces content dynamically
