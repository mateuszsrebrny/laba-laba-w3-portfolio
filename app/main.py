from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import get_git_commit
from app.database import get_db
from app.models import Token, Transaction


class TokenCreate(BaseModel):
    token: str
    is_stable: bool


class TransactionCreate(BaseModel):
    timestamp: datetime
    from_token: str
    to_token: str
    from_amount: float
    to_amount: float


app = FastAPI()
templates = Jinja2Templates(directory="app/templates")


def format_datetime_for_input(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


templates.env.filters["datetimeformat"] = format_datetime_for_input


class FormDataMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Only process specific POST endpoints with form data
        if request.method == "POST" and request.url.path == "/tokens":
            content_type = request.headers.get("Content-Type", "")

            # Handle form data submissions
            if (
                "application/x-www-form-urlencoded" in content_type
                or "multipart/form-data" in content_type
            ):
                try:
                    # Get form data
                    form_data = await request.form()
                    form_dict = dict(form_data)

                    # Process boolean values (convert from strings)
                    if "is_stable" in form_dict:
                        form_dict["is_stable"] = (
                            form_dict["is_stable"].lower() == "true"
                        )

                    # Save the processed data for later use
                    request.state.form_data = form_dict
                except Exception as e:
                    print(f"Error processing form data: {e}")
                    # Don't raise - let the normal request handling catch this

        # Continue with normal request processing
        return await call_next(request)


# Register the middleware
app.add_middleware(FormDataMiddleware)


# Home page - Show transactions
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: Session = Depends(get_db),
    commit: str = Depends(get_git_commit),
):
    transactions = db.query(Transaction).all()
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request, "git_commit": commit, "transactions": transactions},
    )


# Add transaction form
@app.get("/add", response_class=HTMLResponse)
async def add_transaction_page(request: Request, commit: str = Depends(get_git_commit)):
    return templates.TemplateResponse(
        request,
        "add_transaction.html",
        {"request": request, "git_commit": commit, "now": datetime.utcnow()},
    )


def process_add_transaction(
    timestamp: datetime,
    from_token: str,
    to_token: str,
    from_amount: float,
    to_amount: float,
    db: Session,
):
    """Process a transaction between two tokens."""
    # Validate that tokens exist and get their stability status
    from_token_obj = db.query(Token).filter(Token.name == from_token).first()
    to_token_obj = db.query(Token).filter(Token.name == to_token).first()

    # Check if both tokens exist
    if not from_token_obj:
        return JSONResponse(
            content={
                "error": f"'{from_token}' is not recognized. Please add it first."
            },
            status_code=400,
        )
    if not to_token_obj:
        return JSONResponse(
            content={"error": f"'{to_token}' is not recognized. Please add it first."},
            status_code=400,
        )

    # Check if one and only one token is a stablecoin
    if from_token_obj.is_stable and to_token_obj.is_stable:
        return JSONResponse(
            content={"error": "Both tokens cannot be stablecoins"},
            status_code=400,
        )
    if not from_token_obj.is_stable and not to_token_obj.is_stable:
        return JSONResponse(
            content={"error": "One of the tokens must be a stablecoin"},
            status_code=400,
        )

    # Determine which is the stablecoin and which is the non-stablecoin
    if from_token_obj.is_stable:
        stablecoin = from_token
        non_stablecoin = to_token
        stablecoin_amount = from_amount
        non_stablecoin_amount = to_amount
    else:
        stablecoin = to_token
        non_stablecoin = from_token
        stablecoin_amount = to_amount
        non_stablecoin_amount = from_amount

    # Determine if it's a buy or sell of the non-stablecoin
    if from_token_obj.is_stable:
        # Buying non-stablecoin with stablecoin
        final_amount = non_stablecoin_amount  # Positive for buy
        final_usd = stablecoin_amount  # Positive USD amount
    else:
        # Selling non-stablecoin for stablecoin
        final_amount = -non_stablecoin_amount  # Negative for sell
        final_usd = -stablecoin_amount  # Negative USD amount

    # Create and save the transaction
    try:
        new_transaction = Transaction(
            timestamp=timestamp,
            token=non_stablecoin,
            amount=final_amount,
            stable_coin=stablecoin,
            total_usd=final_usd,
        )
        db.add(new_transaction)
        db.commit()
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            content={
                "error": f"'{non_stablecoin}' already has a transaction at '{timestamp}'"
            },
            status_code=409,
        )

    return {
        "status": "success",
        "message": f"Transaction with timestamp '{timestamp}', token '{non_stablecoin}', amount '{final_amount}', stable_coin '{stablecoin}', and total_usd '{final_usd}' added",
    }


# Dependency for data extraction
async def get_transaction_data(request: Request) -> TransactionCreate:
    """Extract transaction data from either JSON or form data based on content type."""
    content_type = request.headers.get("Content-Type", "")

    try:
        if "application/json" in content_type:
            # Handle JSON data
            data = await request.json()
            return TransactionCreate.model_validate(data)
        else:
            # Handle form data
            form = await request.form()

            # Parse timestamp from string
            try:
                timestamp_str = form.get("timestamp")
                timestamp = datetime.fromisoformat(timestamp_str)
            except (ValueError, AttributeError):
                raise HTTPException(status_code=400, detail="Invalid timestamp format")

            # Extract and convert other fields
            try:
                return TransactionCreate(
                    timestamp=timestamp,
                    from_token=form.get("from_token"),
                    to_token=form.get("to_token"),
                    from_amount=float(form.get("from_amount")),
                    to_amount=float(form.get("to_amount")),
                )
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid form data")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=400, detail=f"Error processing request: {str(e)}"
        )


# Single unified endpoint
@app.post("/transactions", response_class=JSONResponse)
async def add_transaction(
    transaction_data: TransactionCreate = Depends(get_transaction_data),
    db: Session = Depends(get_db),
):
    """Add a transaction from either JSON or form data."""
    return process_add_transaction(
        timestamp=transaction_data.timestamp,
        from_token=transaction_data.from_token,
        to_token=transaction_data.to_token,
        from_amount=transaction_data.from_amount,
        to_amount=transaction_data.to_amount,
        db=db,
    )


# Token management endpoints
@app.post("/tokens", response_class=JSONResponse)
async def add_token(
    request: Request,
    token_data: TokenCreate = None,  # For JSON payload
    db: Session = Depends(get_db),
):
    """Add a new token - handles both JSON and form data."""
    try:
        # Handle form data processed by middleware
        if hasattr(request.state, "form_data") and request.state.form_data:
            # Create a Pydantic model from the form data
            data = request.state.form_data
            if not token_data:
                token_data = TokenCreate(
                    token=data.get("token"), is_stable=data.get("is_stable")
                )

        # Return error if we don't have token data
        if not token_data:
            return JSONResponse(
                content={"error": "No valid token data received"}, status_code=400
            )

        # Extract data from the Pydantic model
        token = token_data.token
        is_stable = token_data.is_stable

        # Check if token already exists
        existing_token = db.query(Token).filter(Token.name == token).first()
        if existing_token:
            if existing_token.is_stable != is_stable:
                stability_type = (
                    "stablecoin" if existing_token.is_stable else "non-stablecoin"
                )
                return JSONResponse(
                    content={
                        "error": f"'{token}' is already marked as a {stability_type}."
                    },
                    status_code=409,
                )
            return {"status": "success", "message": f"Token '{token}' already exists"}

        # Create the new token
        new_token = Token(name=token, is_stable=is_stable)
        db.add(new_token)
        db.commit()

        return JSONResponse(
            content={
                "status": "success",
                "message": f"Token '{token}' marked as {'stablecoin' if is_stable else 'non-stablecoin'}",
            },
            headers={"HX-Trigger": "tokenAdded"},
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error processing token: {str(e)}"}, status_code=400
        )


@app.get("/tokens/{token_name}", response_class=JSONResponse)
async def get_token(token_name: str, db: Session = Depends(get_db)):
    token = db.query(Token).filter(Token.name == token_name).first()
    if not token:
        return JSONResponse(
            content={"error": f"Token '{token_name}' not found"},
            status_code=404,
        )
    return {"name": token.name, "is_stable": token.is_stable}


# Token management UI
@app.get("/tokens", response_class=HTMLResponse)
async def tokens_page(
    request: Request,
    db: Session = Depends(get_db),
    commit: str = Depends(get_git_commit),
):
    """Render the tokens management page."""
    tokens = db.query(Token).all()

    # Check if this is an HTMX request for just the token list
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            request, "tokens_list.html", {"request": request, "tokens": tokens}
        )

    # Full page render
    return templates.TemplateResponse(
        request,
        "tokens.html",
        {"request": request, "git_commit": commit, "tokens": tokens},
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "components": {"api": "healthy", "ui": "healthy"}}
