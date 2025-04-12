from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import get_git_commit
from app.database import get_db
from app.models import Token, Transaction

router = APIRouter(prefix="/ui", tags=["UI"])
templates = Jinja2Templates(directory="app/templates")


def format_datetime_for_input(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


templates.env.filters["datetimeformat"] = format_datetime_for_input


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: Session = Depends(get_db),
    commit: str = Depends(get_git_commit),
):
    transactions = db.query(Transaction).all()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "git_commit": commit,
            "transactions": transactions,
        },
    )


@router.get("/add", response_class=HTMLResponse)
async def add_transaction_page(
    request: Request,
    commit: str = Depends(get_git_commit),
):
    return templates.TemplateResponse(
        request,
        "add_transaction.html",
        {
            "request": request,
            "git_commit": commit,
            "now": datetime.utcnow(),
        },
    )


@router.get("/tokens", response_class=HTMLResponse)
async def tokens_page(
    request: Request,
    db: Session = Depends(get_db),
    commit: str = Depends(get_git_commit),
):
    tokens = db.query(Token).all()

    # If using HTMX, return a partial template when requested.
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            request, "tokens_list.html", {"request": request, "tokens": tokens}
        )

    # Full page render
    return templates.TemplateResponse(
        request,
        "tokens.html",
        {
            "request": request,
            "git_commit": commit,
            "tokens": tokens,
        },
    )
