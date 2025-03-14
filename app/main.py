from fastapi import FastAPI, Depends, Request, Form, HTTPException, Security
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security.api_key import APIKeyHeader
from app.database import get_db
from app.models import TokenMetadata, Transaction
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Crypto Transaction Tracker")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
TEST_USERNAME = os.getenv("TEST_USERNAME")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")

def get_valid_credentials():
    return (TEST_USERNAME, TEST_PASSWORD) if os.getenv("TEST_MODE") == "true" else (USERNAME, PASSWORD)

def is_localhost(request: Request) -> bool:
    return request.client.host in ["127.0.0.1", "localhost"]

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    valid_username, valid_password = get_valid_credentials()
    if os.getenv("TEST_MODE") == "true" and not is_localhost(request):
        raise HTTPException(status_code=403, detail="Test credentials can only be used from localhost")
    if username != valid_username or password != valid_password:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    request.session["user"] = username
    return {"message": "Login successful"}

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}

@app.get("/transactions/list")
async def list_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).all()

@app.post("/transactions/add", dependencies=[Depends(api_key_header)])
async def add_transaction(...):
    ...


