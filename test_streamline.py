"""
Quick test script for Streamline API integration

Run this to verify your Streamline credentials work correctly.
Usage: python test_streamline.py

This script uses credentials extracted from the Drupal database.
Token expiration: 2026-03-24
"""

import asyncio
import sys
import os
import json

# Add the app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file (optional, will use hardcoded if not found)
from dotenv import load_dotenv
load_dotenv()


async def test_streamline():
    """Test the Streamline API connection and fetch properties"""
    from app.services.pms.streamline import StreamlineService, StreamlineAPIError
    
    # Credentials extracted from Drupal database
    # PHP serialized format decoded:
    # - crog_rates_token_key: s:32:"6cf808bff5ab6a4910c942cfba84b704";
    # - crog_rates_token_secret: s:40:"0eceda1e285cf20a595a812785a84bd8bbc9efa8";
    # - crog_rates_token_expiration: s:10:"2026-03-24";
    
    STREAMLINE_API_URL = "https://web.streamlinevrs.com/api/json"
    STREAMLINE_TOKEN_KEY = "0f07d63b60e59f660b8d3a284ba25e5b"
    STREAMLINE_TOKEN_SECRET = "b80892d28428c779e4f8a0f6505943c9b6d950e3"
    TOKEN_EXPIRATION = "2026-03-24"
    
    print("=" * 60)
    print("Testing Streamline API Integration")
    print("=" * 60)
    print(f"\nUsing credentials from Drupal database:")
    print(f"  API URL: {STREAMLINE_API_URL}")
    print(f"  Token Key: {STREAMLINE_TOKEN_KEY[:8]}...{STREAMLINE_TOKEN_KEY[-4:]}")
    print(f"  Token Secret: {STREAMLINE_TOKEN_SECRET[:8]}...{STREAMLINE_TOKEN_SECRET[-4:]}")
    print(f"  Token Expiration: {TOKEN_EXPIRATION}")
    
    try:
        # Create service instance with explicit credentials
        service = StreamlineService(
            api_url=STREAMLINE_API_URL,
            token_key=STREAMLINE_TOKEN_KEY,
            token_secret=STREAMLINE_TOKEN_SECRET
        )
        print(f"\n[OK] Service initialized successfully")
        
        # Test getting property list
        print("\n[...] Fetching property list from Streamline API...")
        print("      (This may take a few seconds...)")
        
        properties = await service.get_property_list()
        
        print(f"\n[OK] Successfully retrieved {len(properties)} properties!")
        
        # Display first few properties
        if properties:
            print("\n" + "-" * 60)
            print("Sample Properties (showing first 5):")
            print("-" * 60)
            
            for i, prop in enumerate(properties[:5], 1):
                print(f"\n{i}. Property Details:")
                
                # Try common property ID fields
                prop_id = prop.get('unit_id') or prop.get('id') or prop.get('property_id') or 'N/A'
                print(f"   ID: {prop_id}")
                
                # Try common name fields
                name = prop.get('name') or prop.get('unit_name') or prop.get('property_name') or 'N/A'
                print(f"   Name: {name}")
                
                # Print all available keys for first property to help understand structure
                if i == 1:
                    print(f"   Available fields: {', '.join(sorted(prop.keys()))}")
                
                # Print common fields if they exist
                for key in ['bedrooms', 'bathrooms', 'sleeps', 'sleeps_max', 'location', 'city', 'state', 'address']:
                    if key in prop:
                        print(f"   {key.title()}: {prop[key]}")
            
            if len(properties) > 5:
                print(f"\n... and {len(properties) - 5} more properties")
            
            # Show full response structure for first property (for debugging)
            print("\n" + "-" * 60)
            print("Full response structure for first property:")
            print("-" * 60)
            print(json.dumps(properties[0] if properties else {}, indent=2))
            
        else:
            print("\n[WARN] No properties returned (list is empty)")
            print("       This could mean:")
            print("       - No properties are configured in Streamline")
            print("       - API credentials don't have access")
            print("       - API method name might be incorrect")
        
        print("\n" + "=" * 60)
        print("[OK] Streamline API test PASSED!")
        print("=" * 60)
        return True
        
    except ValueError as e:
        print(f"\n[ERROR] Configuration Error: {e}")
        print("\nThis error usually means credentials are missing or invalid.")
        return False
        
    except StreamlineAPIError as e:
        print(f"\n[ERROR] Streamline API Error: {e.message}")
        if hasattr(e, 'error_code') and e.error_code:
            print(f"   Error Code: {e.error_code}")
        
        # Check for specific IP whitelisting error
        if "cannot access from your IP address" in str(e.message) or (hasattr(e, 'error_code') and e.error_code == "E0012"):
            print("\n" + "=" * 60)
            print("IP WHITELISTING ISSUE DETECTED")
            print("=" * 60)
            print("\nThe Streamline API requires your IP address to be whitelisted.")
            print("This is a security feature that restricts API access to authorized IPs only.")
            print("\nTo resolve this issue:")
            print("  1. Contact StreamlineVRS support to whitelist your IP address")
            print("  2. Provide them with:")
            print("     - Your IP address (shown in the error message)")
            print("     - Your API token key (for account verification)")
            print("     - Your company/account name")
            print("  3. Alternatively, if you have a server/VPS, you can:")
            print("     - Run the API calls from a whitelisted server")
            print("     - Use a VPN or proxy that's already whitelisted")
            print("     - Set up a backend service on a whitelisted IP")
            print("\nNote: The credentials appear to be valid, but IP restrictions")
            print("      are preventing access to the API.")
            print("=" * 60)
        else:
            print("\nPossible causes:")
            print("  - Invalid token_key or token_secret")
            print("  - Token has expired (expires: 2026-03-24)")
            print("  - API endpoint URL is incorrect")
            print("  - Network connectivity issues")
            print("  - IP address not whitelisted (if error mentions IP)")
        return False
        
    except Exception as e:
        print(f"\n[ERROR] Unexpected Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_streamline())
    sys.exit(0 if success else 1)

