import io
import re
import warnings
from datetime import datetime

import easyocr
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel

from app.logic.transactions import process_add_transaction


class ExtractedTransaction(BaseModel):
    timestamp: datetime
    from_token: str
    to_token: str
    from_amount: float
    to_amount: float


def parse_debank_screenshot(text: str):
    """
    Parse text extracted from a Debank screenshot to identify transactions.
    """

    transactions = []
    failures = []
    text = text.replace("\n", " ").replace("\r", " ")

    # Split by "Contract Interaction"
    sections = text.split("Contract Interaction")

    for i, section in enumerate(sections[1:], 1):
        section = section.strip()
        print(f"section: {section}")
        if not section:
            continue

        curr_transaction = {}

        # More flexible regex patterns to handle OCR errors
        from_patterns = [
            r"-\s*(\d+(?:\.\d+)?)\s+([A-Z]+)\s*\([s$]?[\d,.]+\)",
            r"-(\d+(?:\.\d+)?)\s+([A-Z]+)",
        ]

        for pattern in from_patterns:
            from_match = re.search(pattern, section)
            if from_match:
                curr_transaction["from_amount"] = float(from_match.group(1))
                curr_transaction["from_token"] = from_match.group(2)
                break

        to_patterns = [
            r"\+\s*(\d+(?:\.\d+)?)\s+([A-Z]+)\s*\(\$[\d,.]+\)",
            r"\+(\d+(?:\.\d+)?)\s+([A-Z]+)",
        ]

        for pattern in to_patterns:
            to_match = re.search(pattern, section)
            if to_match:
                curr_transaction["to_amount"] = float(to_match.group(1))
                curr_transaction["to_token"] = to_match.group(2)
                break

        # Handle timestamp with flexible separators
        timestamp_patterns = [
            r"(\d{4}/\d{2}/\d{2})\s+(\d{2})[.:](\d{2})[.:](\d{2})",
            r"(\d{4}/\d{2}/\d{2})\s+(\d{1,2})[.:](\d{2})[.:](\d{2})",
        ]

        for pattern in timestamp_patterns:
            timestamp_match = re.search(pattern, section)
            if timestamp_match:
                try:
                    date_part = timestamp_match.group(1)
                    hour = timestamp_match.group(2).zfill(2)
                    minute = timestamp_match.group(3)
                    second = timestamp_match.group(4)
                    timestamp_str = f"{date_part} {hour}:{minute}:{second}"
                    curr_transaction["timestamp"] = datetime.strptime(
                        timestamp_str, "%Y/%m/%d %H:%M:%S"
                    )
                    break
                except ValueError:
                    print(f"Failed to parse: {timestamp_str}")
                    continue
            else:
                print(f"No timestamp match in: {section}")

        required_keys = [
            "timestamp",
            "from_token",
            "to_token",
            "from_amount",
            "to_amount",
        ]

        # If we have all required fields, add the transaction
        if all(k in curr_transaction for k in required_keys):
            try:
                transactions.append(ExtractedTransaction(**curr_transaction))
            except Exception as e:
                failures.append({"section": section, "error": str(e)})
        else:
            missing = [k for k in required_keys if k not in curr_transaction]
            failures.append(
                {"section": section, "error": f"Missing fields: {', '.join(missing)}"}
            )

    return transactions, failures


def get_extracted_text(contents: bytes) -> str:
    img = Image.open(io.BytesIO(contents))
    warnings.filterwarnings("ignore", message=".*pin_memory.*no accelerator.*")
    reader = easyocr.Reader(["en"], download_enabled=False, gpu=False)
    result = reader.readtext(img)
    return " ".join([text[1] for text in result])


async def extract_transactions_from_image_upload(image: UploadFile, db):
    contents = await image.read()
    extracted_text = get_extracted_text(contents)
    transactions, parse_failures = parse_debank_screenshot(extracted_text)

    if not transactions:
        return JSONResponse(
            content={
                "status": "info",
                "message": "No transactions found in the image. Extracted: "
                + extracted_text,
            },
            status_code=200,
        )

    # Process and save each transaction
    results = []
    failures = list(parse_failures)
    for t in transactions:
        try:
            result = process_add_transaction(
                timestamp=t.timestamp,
                from_token=t.from_token,
                to_token=t.to_token,
                from_amount=t.from_amount,
                to_amount=t.to_amount,
                db=db,
            )
            results.append(
                {
                    "status": "success",
                    **result,
                    "message": f"Transaction added: {result}",
                }
            )
        except Exception as e:
            failures.append({"section": str(t), "error": str(e)})

    # Count successful transactions
    successful = sum(
        1 for r in results if isinstance(r, dict) and r.get("status") == "success"
    )

    return {
        "status": "success" if successful > 0 else "info",
        "message": f"Added {successful} out of {len(transactions)} transactions from the image.",
        "details": results,
        "failed": failures,
    }
