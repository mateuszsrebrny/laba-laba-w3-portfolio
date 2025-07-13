import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PortfolioLoader:

    def __init__(self, base_url: str = None):
        # Use environment variable or fallback to default
        self.base_url = (
            base_url or os.getenv("API_BASE_URL", "https://laba-laba.onrender.com")
        ).rstrip("/")
        self.extract_endpoint = f"{self.base_url}/api/transactions/extract"
        print(f"Using API endpoint: {self.extract_endpoint}")

        self.successful_transactions = []
        self.errors = []

    async def extract_transaction(
        self, session: aiohttp.ClientSession, image_path: str
    ) -> Dict[str, Any]:
        """Extract transaction data from a single screenshot using multipart form data"""
        try:
            with open(image_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field(
                    "image",
                    f,
                    filename=os.path.basename(image_path),
                    content_type="image/jpeg",
                )  # Adjust based on your image type

                async with session.post(self.extract_endpoint, data=data) as response:

                    if response.status == 200:
                        result = await response.json()

                        # Check if the response indicates success
                        if result.get("status") == "success":
                            return {
                                "status": "success",
                                "image_path": image_path,
                                "data": result,
                                "transactions_found": len(result.get("details", [])),
                            }
                        else:
                            # Handle cases where image processed but no transactions found
                            return {
                                "status": "no_transactions",
                                "image_path": image_path,
                                "message": result.get(
                                    "message", "No transactions found"
                                ),
                                "data": result,
                            }

                    else:
                        error_detail = await response.json()
                        return {
                            "status": "error",
                            "image_path": image_path,
                            "error": f"HTTP {response.status}",
                            "message": error_detail,
                        }

        except Exception as e:
            return {"status": "error", "image_path": image_path, "error": str(e)}

    async def process_screenshots(
        self, screenshot_paths: List[str], max_concurrent: int
    ) -> None:
        """Process multiple screenshots concurrently"""
        timeout_seconds = int(os.getenv("REQUEST_TIMEOUT", "60"))

        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single(session: aiohttp.ClientSession, path: str):
            async with semaphore:
                return await self.extract_transaction(session, path)

        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            tasks = [process_single(session, path) for path in screenshot_paths]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.errors.append(
                        {
                            "status": "error",
                            "image_path": screenshot_paths[i],
                            "error": str(result),
                        }
                    )
                    print(
                        f"❌ Exception processing {os.path.basename(screenshot_paths[i])}: {result}"
                    )
                    continue

                filename = os.path.basename(result["image_path"])

                if result["status"] == "success":
                    self.successful_transactions.append(result)
                    tx_count = result.get("transactions_found", 0)
                    print(
                        f"✅ Successfully processed: {filename} ({tx_count} transactions found)"
                    )

                elif result["status"] == "no_transactions":
                    # These might be considered successful OCR but no transactions
                    self.successful_transactions.append(result)
                    print(f"⚠️  Processed but no transactions: {filename}")

                else:
                    self.errors.append(result)
                    print(f"❌ Error processing {filename}: {result['error']}")

    def get_image_files(
        self, directory: str, extensions: List[str] = None
    ) -> List[str]:
        """Get all image files from a directory"""
        if extensions is None:
            extensions = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]

        image_files = []
        directory_path = Path(directory)

        if not directory_path.exists():
            print(f"Directory {directory} does not exist!")
            return []

        for ext in extensions:
            image_files.extend(directory_path.glob(f"*{ext}"))
            image_files.extend(directory_path.glob(f"*{ext.upper()}"))

        return [str(path) for path in sorted(image_files)]

    def save_results(self, output_file: str = "extraction_results.json") -> None:
        """Save results to a JSON file"""
        # Extract actual transaction details
        all_transactions = []
        for success in self.successful_transactions:
            if success.get("data", {}).get("details"):
                for tx in success["data"]["details"]:
                    tx["source_image"] = os.path.basename(success["image_path"])
                    all_transactions.append(tx)

        results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_images_processed": len(self.successful_transactions)
                + len(self.errors),
                "successful_extractions": len(self.successful_transactions),
                "total_transactions_found": len(all_transactions),
                "errors": len(self.errors),
            },
            "transactions": all_transactions,
            "successful_extractions": self.successful_transactions,
            "errors": self.errors,
        }

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n📊 Results saved to {output_file}")

    def print_summary(self) -> None:
        """Print a detailed summary of the extraction process"""
        total_images = len(self.successful_transactions) + len(self.errors)
        success_rate = (
            (len(self.successful_transactions) / total_images * 100)
            if total_images > 0
            else 0
        )

        # Count total transactions
        total_transactions = 0
        for success in self.successful_transactions:
            if success.get("data", {}).get("details"):
                total_transactions += len(success["data"]["details"])

        print(f"\n{'='*60}")
        print("DEBANK TRANSACTION EXTRACTION SUMMARY")
        print(f"{'='*60}")
        print(f"Total screenshots processed: {total_images}")
        print(f"Successful OCR extractions: {len(self.successful_transactions)}")
        print(f"Total transactions found: {total_transactions}")
        print(f"Errors: {len(self.errors)}")
        print(f"Success rate: {success_rate:.1f}%")

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {os.path.basename(error['image_path'])}: {error['error']}")

        if self.successful_transactions:
            print("\n✅ SUCCESSFUL EXTRACTIONS:")
            for success in self.successful_transactions:
                filename = os.path.basename(success["image_path"])
                data = success.get("data", {})

                if data.get("details"):
                    tx_count = len(data["details"])
                    print(f"  - {filename}: {tx_count} transactions")

                    # Show first few transaction details
                    for i, tx in enumerate(data["details"][:3]):  # Show first 3
                        if "timestamp" in tx:
                            print(f"    • {tx.get('timestamp', 'N/A')}")
                        if i == 2 and len(data["details"]) > 3:
                            print(f"    • ... and {len(data['details']) - 3} more")
                            break
                else:
                    print(f"  - {filename}: No transactions found")


async def main():
    # Load configuration from environment variables
    screenshots_directory = os.getenv("SCREENSHOTS_DIRECTORY", "screens")
    max_concurrent = int(os.getenv("MAX_CONCURRENT_REQUESTS", "1"))

    # Initialize loader
    loader = PortfolioLoader()

    # Get all screenshot files
    screenshot_paths = loader.get_image_files(screenshots_directory)

    if not screenshot_paths:
        print(f"No image files found in {screenshots_directory}")
        print("Please ensure your screenshots are in the correct directory.")
        return

    print(f"Found {len(screenshot_paths)} screenshots to process")
    print("Starting extraction process...")

    # Process screenshots
    await loader.process_screenshots(screenshot_paths, max_concurrent=max_concurrent)

    # Print summary and save results
    loader.print_summary()
    loader.save_results()

    print(
        "\n🎉 Processing complete! Check extraction_results.json for detailed results."
    )


if __name__ == "__main__":
    asyncio.run(main())
