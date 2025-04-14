from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api import TokenCreate, TransactionCreate, add_token_api, add_transaction_api
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


@router.get("/transactions/form", response_class=HTMLResponse)
async def transaction_form(request: Request):
    return templates.TemplateResponse(
        "add_transaction_form.html",
        {
            "request": request,
            "now": datetime.utcnow(),
        },
    )


@router.post("/transactions", response_class=JSONResponse)
async def add_transaction_form(
    request: Request,
    timestamp: str = Form(...),
    from_token: str = Form(...),
    to_token: str = Form(...),
    from_amount: float = Form(...),
    to_amount: float = Form(...),
    db: Session = Depends(get_db),
):
    """
    This UI endpoint accepts form data for a transaction, repacks the data into a TransactionCreate model,
    and then calls add_transaction_api internally.
    """
    # Parse the timestamp. The form sends a string; adjust the format as needed.
    try:
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return JSONResponse(
            content={"error": f"Invalid timestamp format: {e}"}, status_code=400
        )

    # Create the TransactionCreate model instance using form data.
    transaction_data = TransactionCreate(
        timestamp=dt,
        from_token=from_token,
        to_token=to_token,
        from_amount=from_amount,
        to_amount=to_amount,
    )

    # Call the existing API logic and return its response.
    return await add_transaction_api(transaction_data, db)


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


@router.post("/tokens", response_class=JSONResponse)
async def add_token_form(
    request: Request,
    token: str = Form(...),
    is_stable: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Handle the form submission on /ui/tokens.

    Convert form data into a TokenCreate model and call the API logic directly.
    """
    # Construct the TokenCreate model from the form data.
    token_create = TokenCreate(token=token, is_stable=(is_stable.lower() == "true"))
    # Call your API route logic internally.
    return await add_token_api(token_create, db)
