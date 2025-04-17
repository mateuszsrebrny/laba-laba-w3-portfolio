from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Token, Transaction

router = APIRouter(prefix="/api", tags=["API"])


class TokenCreate(BaseModel):
    token: str
    is_stable: bool


class TransactionCreate(BaseModel):
    timestamp: datetime
    from_token: str
    to_token: str
    from_amount: float
    to_amount: float


def process_add_transaction(
    timestamp: datetime,
    from_token: str,
    to_token: str,
    from_amount: float,
    to_amount: float,
    db: Session,
):
    # Validate that tokens exist and get their stability status
    from_token_obj = db.query(Token).filter(Token.name == from_token).first()
    to_token_obj = db.query(Token).filter(Token.name == to_token).first()

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
        final_amount = non_stablecoin_amount  # Positive for buy
        final_usd = stablecoin_amount
    else:
        final_amount = -non_stablecoin_amount  # Negative for sell
        final_usd = -stablecoin_amount

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
                "error": f"Transaction for '{non_stablecoin}' at '{timestamp}' already exists."
            },
            status_code=409,
        )

    return {
        "status": "success",
        "message": f"Transaction added: timestamp '{timestamp}', token '{non_stablecoin}', amount '{final_amount}', stable_coin '{stablecoin}', total_usd '{final_usd}'.",
    }


@router.post("/transactions", response_class=JSONResponse)
async def add_transaction_api(
    transaction_data: TransactionCreate, db: Session = Depends(get_db)
):
    return process_add_transaction(
        timestamp=transaction_data.timestamp,
        from_token=transaction_data.from_token,
        to_token=transaction_data.to_token,
        from_amount=transaction_data.from_amount,
        to_amount=transaction_data.to_amount,
        db=db,
    )


@router.post("/tokens", response_class=JSONResponse)
async def add_token_api(token_data: TokenCreate, db: Session = Depends(get_db)):
    token = token_data.token
    is_stable = token_data.is_stable

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


@router.get("/tokens/{token_name}", response_class=JSONResponse)
async def get_token(token_name: str, db: Session = Depends(get_db)):
    token = db.query(Token).filter(Token.name == token_name).first()
    if not token:
        return JSONResponse(
            content={"error": f"Token '{token_name}' not found."},
            status_code=404,
        )
    return {"name": token.name, "is_stable": token.is_stable}
