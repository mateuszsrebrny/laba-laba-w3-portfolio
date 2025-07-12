import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Set

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TokenManager:
    def __init__(self, base_url: str = None):
        # Use environment variable or fallback to default
        self.base_url = (base_url or 
                        os.getenv('API_BASE_URL', 'https://laba-laba.onrender.com')).rstrip('/')
        self.tokens_endpoint = f"{self.base_url}/api/tokens"
        self.unrecognized_tokens = set()
        print(f"Using API base URL: {self.base_url}")
        
    def extract_unrecognized_tokens_from_results(self, extraction_results: Dict) -> Set[str]:
        """Extract tokens that need to be added from extraction results"""
        tokens = set()
        
        # Check details array for unrecognized token errors
        for detail in extraction_results.get('details', []):
            if detail.get('status') == 'error':
                error_msg = detail.get('error', '')
                # Pattern: "'TOKEN' is not recognized. Please add it first."
                match = re.search(r"'([a-zA-Z0-9]+)' is not recognized", error_msg)
                if match:
                    token_symbol = match.group(1)
                    tokens.add(token_symbol)
                    print(f"Found unrecognized token: {token_symbol}")
        
        # Also check failed array if it exists
        for failed_item in extraction_results.get('failed', []):
            if isinstance(failed_item, dict) and 'error' in failed_item:
                error_msg = failed_item.get('error', '')
                match = re.search(r"'([a-zA-Z0-9]+)' is not recognized", error_msg)
                if match:
                    token_symbol = match.group(1)
                    tokens.add(token_symbol)
                    print(f"Found unrecognized token in failed: {token_symbol}")
        
        return tokens
    

    def load_tokens_from_file(self, results_file: str = None) -> Set[str]:
        """Load and extract unrecognized tokens from saved extraction results"""
        if results_file is None:
             results_file = os.getenv('RESULTS_FILE', 'extraction_results.json')
         
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
            
            all_tokens = set()
            
            # Process successful extractions that had errors
            for success in data.get('successful_extractions', []):
                tokens = self.extract_unrecognized_tokens_from_results(success.get('data', {}))
                all_tokens.update(tokens)
            
            # Process errors
            for error in data.get('errors', []):
                if 'data' in error:
                    tokens = self.extract_unrecognized_tokens_from_results(error['data'])
                    all_tokens.update(tokens)
            
            return all_tokens
            
        except FileNotFoundError:
            print(f"Results file {results_file} not found")
            return set()
        except json.JSONDecodeError:
            print(f"Invalid JSON in {results_file}")
            return set()
    
    def get_stablecoin_decision(self, token: str) -> bool:
        """Interactive function to ask user if token is a stablecoin"""
        # Common stablecoins for auto-detection
        known_stablecoins = {
            'USDC', 'USDT', 'DAI', 'BUSD', 'TUSD', 'USDP', 'FRAX', 
            'LUSD', 'sUSD', 'GUSD', 'HUSD', 'USDN', 'UST', 'USTC',
			'MAI', 'GHO', 
        }
        
        if token.upper() in known_stablecoins:
            print(f"✅ Auto-detected {token} as stablecoin")
            return True
        
        while True:
            response = input(f"Is '{token}' a stablecoin? (y/n/skip): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            elif response in ['s', 'skip']:
                print(f"Skipping {token}")
                return None
            else:
                print("Please enter 'y' for yes, 'n' for no, or 'skip' to skip this token")
    
    async def add_token(self, session: aiohttp.ClientSession, token: str, is_stable: bool) -> Dict:
        """Add a single token via the API"""
        payload = {
            "token": token,
            "is_stable": is_stable
        }
        
        try:
            async with session.post(
                self.tokens_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if response.status in [200, 201]:
                    return {
                        "status": "success",
                        "token": token,
                        "is_stable": is_stable,
                        "response": result,
                        "http_status": response.status
                    }
                else:
                    return {
                        "status": "error",
                        "token": token,
                        "is_stable": is_stable,
                        "error": result,
                        "http_status": response.status
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "token": token,
                "is_stable": is_stable,
                "error": str(e),
                "http_status": None
            }
    
    async def add_tokens_batch(self, tokens_with_stability: List[tuple]) -> Dict:
        """Add multiple tokens to the system"""
        results = {
            "successful": [],
            "failed": [],
            "skipped": []
        }
        
        async with aiohttp.ClientSession() as session:
            for token, is_stable in tokens_with_stability:
                if is_stable is None:  # Skipped
                    results["skipped"].append(token)
                    continue
                
                print(f"Adding {token} (stablecoin: {is_stable})...")
                result = await self.add_token(session, token, is_stable)
                
                if result["status"] == "success":
                    results["successful"].append(result)
                    status_text = "stablecoin" if is_stable else "non-stablecoin"
                    print(f"✅ Successfully added {token} as {status_text}")
                else:
                    results["failed"].append(result)
                    print(f"❌ Failed to add {token}: {result.get('error', 'Unknown error')}")
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.5)
        
        return results
    
    def print_summary(self, results: Dict):
        """Print a summary of the token addition process"""
        print(f"\n{'='*50}")
        print(f"TOKEN ADDITION SUMMARY")
        print(f"{'='*50}")
        print(f"Successfully added: {len(results['successful'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Skipped: {len(results['skipped'])}")
        
        if results['successful']:
            print(f"\n✅ SUCCESSFULLY ADDED:")
            for result in results['successful']:
                status_text = "stablecoin" if result['is_stable'] else "non-stablecoin"
                print(f"  - {result['token']} ({status_text})")
        
        if results['failed']:
            print(f"\n❌ FAILED TO ADD:")
            for result in results['failed']:
                print(f"  - {result['token']}: {result.get('error', 'Unknown error')}")
        
        if results['skipped']:
            print(f"\n⏭️ SKIPPED:")
            for token in results['skipped']:
                print(f"  - {token}")

async def main():

    # Initialize token manager with environment variables
    token_manager = TokenManager()
    


    # Option 1: Extract from saved results file
    # Load configuration from environment
    results_file = os.getenv('RESULTS_FILE', 'extraction_results.json')
    
    print("Loading unrecognized tokens from extraction results...")
    unrecognized_tokens = token_manager.load_tokens_from_file(results_file)
    
    # Option 2: Manual token list (if you want to add specific tokens)
    # unrecognized_tokens = {'ETH', 'BTC', 'MATIC'}  # Add your tokens here
    
    if not unrecognized_tokens:
        print("No unrecognized tokens found. Make sure you have run the extraction script first.")
        return
    
    print(f"\nFound {len(unrecognized_tokens)} unrecognized tokens:")
    for token in sorted(unrecognized_tokens):
        print(f"  - {token}")
    
    # Get user decisions for each token
    print(f"\n{'='*50}")
    print("STABLECOIN CLASSIFICATION")
    print("Please classify each token as stablecoin or not:")
    print("(Most crypto tokens are NOT stablecoins)")
    print(f"{'='*50}")
    
    tokens_with_stability = []
    for token in sorted(unrecognized_tokens):
        is_stable = token_manager.get_stablecoin_decision(token)
        tokens_with_stability.append((token, is_stable))
    
    # Add tokens via API
    print(f"\n{'='*50}")
    print("ADDING TOKENS TO SYSTEM")
    print(f"{'='*50}")
    
    results = await token_manager.add_tokens_batch(tokens_with_stability)
    
    # Print summary
    token_manager.print_summary(results)

    # Save results
    output_file = os.getenv('TOKEN_ADDITION_RESULTS_FILE', 'token_addition_results.json')
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nðDetailed results saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())

