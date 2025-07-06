from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.encoders import jsonable_encoder
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
    result = process_add_transaction(
        timestamp=transaction_data.timestamp,
        from_token=transaction_data.from_token,
        to_token=transaction_data.to_token,
        from_amount=transaction_data.from_amount,
        to_amount=transaction_data.to_amount,
        db=db,
    )

    #    status_code = (
    #        result.get("status_code", status.HTTP_201_CREATED)
    #        if result.get("status") != "error"
    #        else result.get("status_code", status.HTTP_400_BAD_REQUEST)
    #    )

    encoded_result = jsonable_encoder(result)

    if result.get("status") == "error":
        # Fall back to 400 if no specific code was supplied
        return JSONResponse(
            content=encoded_result,
            status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
        )

    return JSONResponse(content=encoded_result, status_code=status.HTTP_201_CREATED)


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


@router.post(
    "/transactions/extract",
    response_class=JSONResponse,
    summary="Extract transactions from Debank screenshot",
    description="Process a Debank screenshot image to automatically extract and add cryptocurrency transactions to your portfolio using OCR",
    responses={
        200: {
            "description": "Image processed successfully (may contain successful transactions, failures, or no transactions found)",
            "content": {
                "application/json": {
                    "examples": {
                        "successful_extraction": {
                            "summary": "Transactions successfully extracted and processed",
                            "value": {
                                "status": "success",
                                "message": "Added 2 out of 2 transactions from the image.",
                                "details": [
                                    {
                                        "status": "success",
                                        "id": 123,
                                        "timestamp": "2025-07-06T10:30:00",
                                        "from_token": "USDC",
                                        "to_token": "ETH",
                                        "from_amount": 1000.0,
                                        "to_amount": 0.3,
                                        "message": "Transaction added: {...}",
                                    }
                                ],
                                "failed": [],
                            },
                        },
                        "partial_success": {
                            "summary": "Some transactions processed, some failed",
                            "value": {
                                "status": "success",
                                "message": "Added 1 out of 2 transactions from the image.",
                                "details": [
                                    {
                                        "status": "success",
                                        "id": 124,
                                        "timestamp": "2025-07-06T11:00:00",
                                        "from_token": "ETH",
                                        "to_token": "USDC",
                                        "from_amount": 0.5,
                                        "to_amount": 1500.0,
                                        "message": "Transaction added: {...}",
                                    }
                                ],
                                "failed": [
                                    {
                                        "section": "Contract Interaction...",
                                        "error": "Missing fields: timestamp",
                                    }
                                ],
                            },
                        },
                        "no_transactions_found": {
                            "summary": "No transactions detected in image",
                            "value": {
                                "status": "info",
                                "message": "No transactions found in the image. Extracted: Contract Interaction some text but no valid transaction pattern",
                            },
                        },
                    }
                }
            },
        },
        400: {
            "description": "Invalid file format",
            "content": {
                "application/json": {
                    "example": {"error": "Invalid file format. Please upload an image."}
                }
            },
        },
        500: {
            "description": "Internal server error during image processing",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Failed to process image: OCR processing failed"
                    }
                }
            },
        },
    },
)
async def extract_transactions_from_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Extract and process cryptocurrency transactions from a Debank screenshot using OCR.

    This endpoint uses EasyOCR to automatically extract transaction data from uploaded
    Debank screenshots and processes them through the same validation logic as manual entries.

    ## How It Works
    1. **OCR Processing**: Extracts text from the uploaded image using EasyOCR
    2. **Pattern Matching**: Searches for "Contract Interaction" sections in the extracted text
    3. **Transaction Parsing**: Uses regex patterns to identify:
       - Amounts with +/- signs and token symbols
       - Timestamps in format YYYY/MM/DD HH:MM:SS
       - Token pairs for swaps
    4. **Validation & Storage**: Each extracted transaction is validated and saved to database

    ## Expected Image Format
    The image should contain Debank transaction data with:
    - **Contract Interaction** headers separating transactions
    - **Amount patterns** like: `+1000.50 USDC ($1,000.50)` or `-0.5 ETH ($1,500.00)`
    - **Timestamps** in format: `2025/07/06 10:30:45`
    - Clear, readable text (avoid blurry or low-resolution images)

    ## Response Structure

    ### Success Response
    - `status`: "success" (if any transactions added) or "info" (if none found)
    - `message`: Summary of processing results
    - `details`: Array of successfully processed transactions with full transaction data
    - `failed`: Array of parsing failures with error descriptions

    ### Transaction Details Include
    - `id`: Database ID of the created transaction
    - `timestamp`: Parsed transaction timestamp
    - `from_token`/`to_token`: Token symbols involved in the swap
    - `from_amount`/`to_amount`: Amounts for each token
    - `status`: "success" for successfully added transactions

    ## Common Parsing Scenarios
    - **Explicit Signs**: `+1000 USDC` and `-0.5 ETH` → Clear buy/sell direction
    - **Mixed Signs**: `+1000 USDC` and `0.5 ETH` → Unsigned amount treated as outgoing
    - **Missing Data**: Transactions missing timestamps or amounts will appear in `failed` array

    ## Error Handling
    - **Parse Failures**: Individual transaction parsing errors are collected in `failed` array
    - **Validation Errors**: Database validation failures (missing tokens, etc.) are included
    - **OCR Issues**: Poor image quality may result in no transactions found

    ## Tips for Best Results
    - Use high-resolution, clear screenshots
    - Ensure good contrast between text and background
    - Crop images to focus on transaction data
    - Include complete transaction information (timestamps, amounts, tokens)
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
