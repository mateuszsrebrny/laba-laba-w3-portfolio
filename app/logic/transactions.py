from datetime import datetime

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Token, Transaction


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
        dict: Success message on success, or error response on failure

    Raises:
        IntegrityError: If a transaction with the same token and timestamp already exists
    """
    # Validate that tokens exist and get their stability status
    from_token_obj = db.query(Token).filter(Token.name == from_token).first()
    to_token_obj = db.query(Token).filter(Token.name == to_token).first()

    if not from_token_obj:
        return {
            "status": "error",
            "error": f"'{from_token}' is not recognized. Please add it first.",
            "status_code": status.HTTP_400_BAD_REQUEST,
        }
    if not to_token_obj:
        return {
            "status": "error",
            "error": f"'{to_token}' is not recognized. Please add it first.",
            "status_code": status.HTTP_400_BAD_REQUEST,
        }
    if from_token_obj.is_stable and to_token_obj.is_stable:
        return {
            "status": "error",
            "error": f"Both tokens cannot be stablecoins ('{from_token}' and '{to_token}' are)",
            "status_code": status.HTTP_400_BAD_REQUEST,
        }
    if not from_token_obj.is_stable and not to_token_obj.is_stable:
        return {
            "status": "error",
            "error": f"One of the tokens must be a stablecoin ('{from_token}' and '{to_token}' are not)",
            "status_code": status.HTTP_400_BAD_REQUEST,
        }

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
        return {
            "status": "error",
            "error": f"Transaction for '{non_stablecoin}' at '{timestamp}' already exists.",
            "status_code": status.HTTP_409_CONFLICT,
        }

    return {
        "status": "success",
        "timestamp": timestamp,
        "token": non_stablecoin,
        "amount": final_amount,
        "stable_coin": stablecoin,
        "total_usd": final_usd,
        "message": f"Transaction added: timestamp '{timestamp}', token '{non_stablecoin}', amount '{final_amount}', stable_coin '{stablecoin}', total_usd '{final_usd}'.",
    }
