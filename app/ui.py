from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request, status
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
    """
    Render the main dashboard page showing all transactions.

    This endpoint fetches all transactions from the database and displays them
    in a user-friendly interface.
    """
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
    """
    Render the transaction creation form page.

    This endpoint displays a form allowing users to input transaction details.
    """
    return templates.TemplateResponse(
        request,
        "add_transaction.html",
        {
            "request": request,
            "git_commit": commit,
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
    Handle transaction form submissions from the UI.

    This endpoint:
    1. Parses the timestamp string into a datetime object
    2. Constructs a TransactionCreate model from form data
    3. Calls the API endpoint to process the transaction

    Args:
        Various form fields representing transaction details

    Returns:
        JSONResponse: Result of the transaction processing
    """
    # Parse the timestamp. The form sends a string; adjust the format as needed.
    try:
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return JSONResponse(
            content={"error": f"Invalid timestamp format: {e}"},
            status_code=status.HTTP_400_BAD_REQUEST,
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
    """
    Render the tokens management page.

    This endpoint fetches all tokens from the database and displays them
    in a user-friendly interface. It also handles HTMX partial updates
    for dynamic content refreshing.
    """
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
    Handle token creation form submissions from the UI.

    This endpoint:
    1. Converts form string data to the appropriate types
    2. Constructs a TokenCreate model
    3. Calls the API endpoint to process the token creation

    Args:
        token (str): The token symbol/name
        is_stable (str): String "true" or "false" indicating if token is stable

    Returns:
        JSONResponse: Result of the token creation process
    """
    # Construct the TokenCreate model from the form data.
    token_create = TokenCreate(token=token, is_stable=(is_stable.lower() == "true"))
    # Call your API route logic internally.
    return await add_token_api(token_create, db)
