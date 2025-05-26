from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.logic.transactions import process_add_transaction
from app.models import Token
from app.ocr import extract_transactions_from_image_upload

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
                status_code=status.HTTP_409_CONFLICT,
            )
        # Token exists with matching data - return 200 OK
        return JSONResponse(
            content={"status": "success", "message": f"Token '{token}' already exists"},
            status_code=status.HTTP_200_OK,
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
        status_code=status.HTTP_201_CREATED,
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
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return {"name": token.name, "is_stable": token.is_stable}


@router.post("/transactions/extract", response_class=JSONResponse)
async def extract_transactions_from_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Extract transactions from a Debank screenshot and process them.
    """
    # Validate file is an image
    if not image.content_type or not image.content_type.startswith("image/"):
        return JSONResponse(
            content={"error": "Invalid file format. Please upload an image."},
            status_code=400,
        )

    try:

        return await extract_transactions_from_image_upload(image, db)

    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to process image: {str(e)}"},
            status_code=500,
        )
