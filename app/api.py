from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Token, Transaction

router = APIRouter(prefix="/api", tags=["API"])


class TokenCreate(BaseModel):
    """
    Schema for creating a new token.

    Attributes:
        token (str): The name/symbol of the token
        is_stable (bool): Whether the token is a stablecoin (true) or not (false)
    """

    token: str
    is_stable: bool

    model_config = ConfigDict(
        json_schema_extra={"example": {"token": "USDC", "is_stable": True}}
    )


class TransactionCreate(BaseModel):
    """
    Schema for creating a new transaction between tokens.

    Attributes:
        timestamp (datetime): When the transaction occurred
        from_token (str): The source token symbol
        to_token (str): The destination token symbol
        from_amount (float): Amount of the source token
        to_amount (float): Amount of the destination token
    """

    timestamp: datetime
    from_token: str
    to_token: str
    from_amount: float
    to_amount: float

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2025-04-18T10:30:00",
                "from_token": "USDC",
                "to_token": "ETH",
                "from_amount": 1000.0,
                "to_amount": 0.5,
            }
        }
    )


def process_add_transaction(
    timestamp: datetime,
    from_token: str,
    to_token: str,
    from_amount: float,
    to_amount: float,
    db: Session,
):
    """
    Process and validate a transaction between two tokens.

    This function implements the business logic for token transactions:
    - Validates that both tokens exist in the database
    - Ensures that exactly one token is a stablecoin
    - Calculates final USD values and token amounts
    - Stores the transaction in the database

    Args:
        timestamp (datetime): When the transaction occurred
        from_token (str): The source token symbol
        to_token (str): The destination token symbol
        from_amount (float): Amount of the source token
        to_amount (float): Amount of the destination token
        db (Session): Database session for querying and saving

    Returns:
        dict or JSONResponse: Success message on success, or error response on failure

    Raises:
        IntegrityError: If a transaction with the same token and timestamp already exists
    """
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
        final_usd = -from_amount
        final_amount = to_amount
    else:
        stablecoin = to_token
        non_stablecoin = from_token
        final_usd = to_amount
        final_amount = -from_amount

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


@router.post(
    "/transactions",
    response_class=JSONResponse,
    status_code=201,
    responses={
        201: {
            "description": "Transaction successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Transaction added: timestamp '2025-04-18 10:30:00', token 'ETH', amount '0.5', stable_coin 'USDC', total_usd '-1000'.",
                    }
                }
            },
        },
        400: {
            "description": "Invalid transaction parameters",
            "content": {
                "application/json": {
                    "example": {"error": "One of the tokens must be a stablecoin"}
                }
            },
        },
        409: {
            "description": "Transaction already exists",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Transaction for 'ETH' at '2025-04-18 10:30:00' already exists."
                    }
                }
            },
        },
    },
)
async def add_transaction_api(
    transaction_data: TransactionCreate, db: Session = Depends(get_db)
):
    """
    Create a new transaction between tokens.

    This endpoint validates that:
    - Both tokens exist
    - One token must be stable and one non-stable
    - The transaction doesn't already exist

    The system will automatically determine which token is the stablecoin and calculate
    the appropriate values for storage.

    Returns:
        JSONResponse: Success confirmation or error details
    """
    return process_add_transaction(
        timestamp=transaction_data.timestamp,
        from_token=transaction_data.from_token,
        to_token=transaction_data.to_token,
        from_amount=transaction_data.from_amount,
        to_amount=transaction_data.to_amount,
        db=db,
    )


@router.post(
    "/tokens",
    response_class=JSONResponse,
    responses={
        201: {
            "description": "Token successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Token 'ETH' marked as non-stablecoin",
                    }
                }
            },
        },
        200: {
            "description": "Token already exists with matching properties",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Token 'USDC' already exists",
                    }
                }
            },
        },
        409: {
            "description": "Token already exists with different stability status",
            "content": {
                "application/json": {
                    "example": {"error": "'USDC' is already marked as a stablecoin."}
                }
            },
        },
    },
)
async def add_token_api(token_data: TokenCreate, db: Session = Depends(get_db)):
    """
    Add a new token to the system.

    This endpoint registers a new token with its stability status.
    - Returns 201 if a new token is created
    - Returns 200 if the token already exists with matching stability status
    - Returns 409 if the token exists with a different stability status

    Returns:
        JSONResponse: Result with appropriate status code
    """
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
        # Token exists with matching data - return 200 OK
        return JSONResponse(
            content={"status": "success", "message": f"Token '{token}' already exists"},
            status_code=200,
            headers={"HX-Trigger": "tokenAdded"},
        )

    # New token creation - use 201 Created
    new_token = Token(name=token, is_stable=is_stable)
    db.add(new_token)
    db.commit()

    return JSONResponse(
        content={
            "status": "success",
            "message": f"Token '{token}' marked as {'stablecoin' if is_stable else 'non-stablecoin'}",
        },
        status_code=201,
        headers={"HX-Trigger": "tokenAdded"},
    )


@router.get(
    "/tokens/{token_name}",
    response_class=JSONResponse,
    responses={
        200: {
            "description": "Token information retrieved successfully",
            "content": {
                "application/json": {"example": {"name": "USDC", "is_stable": True}}
            },
        },
        404: {
            "description": "Token not found",
            "content": {
                "application/json": {"example": {"error": "Token 'UNKNOWN' not found."}}
            },
        },
    },
)
async def get_token(token_name: str, db: Session = Depends(get_db)):
    """
    Retrieve information about a specific token.

    Args:
        token_name (str): The name/symbol of the token to retrieve
        db (Session): Database session dependency

    Returns:
        JSONResponse: Token information or 404 error if not found
    """
    token = db.query(Token).filter(Token.name == token_name).first()
    if not token:
        return JSONResponse(
            content={"error": f"Token '{token_name}' not found."},
            status_code=404,
        )
    return {"name": token.name, "is_stable": token.is_stable}
