"""
Streamline VRS (Vacation Rental Software) API Integration

This module provides methods to interact with Streamline's REST/JSON API
for property management operations.

Streamline uses different API patterns:
1. JSON-RPC style with methodName for some endpoints
2. REST-style with headers for token authentication
"""

import httpx
from typing import Optional, Dict, Any, List
from app.config import settings


class StreamlineAPIError(Exception):
    """Custom exception for Streamline API errors"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class StreamlineService:
    """
    Service class for interacting with Streamline PMS API
    
    Supports both:
    - JSON-RPC style API (POST with methodName in body)
    - REST API style (headers with token_key and token_secret)
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        token_key: Optional[str] = None,
        token_secret: Optional[str] = None
    ):
        self.api_url = api_url or settings.STREAMLINE_API_URL
        self.token_key = token_key or settings.STREAMLINE_TOKEN_KEY
        self.token_secret = token_secret or settings.STREAMLINE_TOKEN_SECRET
        
        if not self.api_url:
            raise ValueError("Streamline API URL is required. Set STREAMLINE_API_URL in your .env file (e.g., https://yourcompany.streamlinevrs.com)")
        if not self.token_key or not self.token_secret:
            raise ValueError("Streamline token_key and token_secret are required")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for REST API calls"""
        return {
            "Content-Type": "application/json",
            "token_key": self.token_key,
            "token_secret": self.token_secret,
        }
    
    async def _make_rest_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a REST API request to Streamline
        
        Args:
            endpoint: The API endpoint (e.g., '/v1/properties')
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            json_body: JSON body for POST/PUT requests
            
        Returns:
            The API response data
        """
        url = f"{self.api_url.rstrip('/')}{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_auth_headers(),
                    params=params,
                    json=json_body
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API-level errors
                if isinstance(data, dict):
                    if data.get("error"):
                        raise StreamlineAPIError(
                            message=data.get("error", "Unknown Streamline API error"),
                            error_code=data.get("error_code")
                        )
                
                return data
                
            except httpx.HTTPStatusError as e:
                raise StreamlineAPIError(
                    message=f"HTTP error {e.response.status_code}: {e.response.text}"
                )
            except httpx.RequestError as e:
                raise StreamlineAPIError(
                    message=f"Request failed: {str(e)}"
                )
    
    async def _make_jsonrpc_request(
        self,
        method_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a JSON-RPC style request to Streamline
        
        Args:
            method_name: The API method to call
            params: Optional parameters for the method
            
        Returns:
            The API response data
        """
        payload = {
            "methodName": method_name,
            "params": {
                "token_key": self.token_key,
                "token_secret": self.token_secret,
                **(params or {})
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API-level errors (Streamline uses status.code format)
                if isinstance(data, dict):
                    # Check for Streamline status object
                    if "status" in data:
                        status = data.get("status", {})
                        if isinstance(status, dict):
                            code = status.get("code")
                            # Code 0 means success, non-zero means error
                            if code is not None and code != 0:
                                raise StreamlineAPIError(
                                    message=status.get("description", "Unknown Streamline API error"),
                                    error_code=str(code)
                                )
                    # Also check for direct error field (fallback)
                    elif data.get("error"):
                        raise StreamlineAPIError(
                            message=data.get("error", "Unknown Streamline API error"),
                            error_code=data.get("error_code")
                        )
                
                return data
                
            except httpx.HTTPStatusError as e:
                raise StreamlineAPIError(
                    message=f"HTTP error {e.response.status_code}: {e.response.text}"
                )
            except httpx.RequestError as e:
                raise StreamlineAPIError(
                    message=f"Request failed: {str(e)}"
                )
    
    async def get_property_list(
        self,
        include_inactive: bool = False,
        property_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of properties from Streamline
        
        Tries REST API first, falls back to JSON-RPC style.
        
        Args:
            include_inactive: Whether to include inactive properties
            property_id: Optional specific property ID to fetch
            
        Returns:
            List of property dictionaries
        """
        params = {}
        
        if property_id:
            params["unit_id"] = property_id
        if include_inactive:
            params["include_inactive"] = "1"
        
        # Try REST API style first
        try:
            response = await self._make_rest_request(
                endpoint="/api/v1/properties",
                params=params if params else None
            )
            
            # Handle different response formats
            if isinstance(response, list):
                return response
            if isinstance(response, dict):
                if "data" in response:
                    return response["data"] if isinstance(response["data"], list) else [response["data"]]
                if "properties" in response:
                    return response["properties"]
                if "result" in response:
                    return response["result"]
            return [response] if response else []
            
        except StreamlineAPIError:
            # Fall back to JSON-RPC style
            pass
        
        # Try JSON-RPC style
        response = await self._make_jsonrpc_request("GetPropertyList", params)
        
        # Handle different response formats
        if isinstance(response, list):
            return response
        if isinstance(response, dict):
            if "data" in response:
                return response["data"] if isinstance(response["data"], list) else [response["data"]]
            if "properties" in response:
                return response["properties"]
            if "result" in response:
                return response["result"]
        
        return [response] if response else []
    
    async def get_property_info(self, property_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific property
        
        Args:
            property_id: The Streamline property/unit ID
            
        Returns:
            Property details dictionary
        """
        # Try REST API first
        try:
            response = await self._make_rest_request(
                endpoint=f"/api/v1/properties/{property_id}"
            )
            return response.get("data", response) if isinstance(response, dict) else response
        except StreamlineAPIError:
            pass
        
        # Fall back to JSON-RPC
        response = await self._make_jsonrpc_request(
            "GetPropertyInfo",
            {"unit_id": property_id}
        )
        
        return response.get("data", response) if isinstance(response, dict) else response
    
    async def get_property_images(self, property_id: int) -> List[Dict[str, Any]]:
        """
        Get images for a specific property
        
        Args:
            property_id: The Streamline property/unit ID
            
        Returns:
            List of image dictionaries
        """
        # Try REST API first
        try:
            response = await self._make_rest_request(
                endpoint=f"/api/v1/properties/{property_id}/images"
            )
            if isinstance(response, list):
                return response
            return response.get("data", response.get("images", [])) if isinstance(response, dict) else []
        except StreamlineAPIError:
            pass
        
        # Fall back to JSON-RPC
        response = await self._make_jsonrpc_request(
            "GetPropertyImages",
            {"unit_id": property_id}
        )
        
        return response.get("data", []) if isinstance(response, dict) else []
    
    async def get_property_amenities(self, property_id: int) -> List[Dict[str, Any]]:
        """
        Get amenities for a specific property
        
        Args:
            property_id: The Streamline property/unit ID
            
        Returns:
            List of amenity dictionaries
        """
        # Try REST API first
        try:
            response = await self._make_rest_request(
                endpoint=f"/api/v1/properties/{property_id}/amenities"
            )
            if isinstance(response, list):
                return response
            return response.get("data", response.get("amenities", [])) if isinstance(response, dict) else []
        except StreamlineAPIError:
            pass
        
        # Fall back to JSON-RPC
        response = await self._make_jsonrpc_request(
            "GetPropertyAmenities",
            {"unit_id": property_id}
        )
        
        return response.get("data", []) if isinstance(response, dict) else []
    
    async def get_availability(
        self,
        property_id: int,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get availability for a property within a date range
        
        Args:
            property_id: The Streamline property/unit ID
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            
        Returns:
            Availability data dictionary
        """
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        # Try REST API first
        try:
            response = await self._make_rest_request(
                endpoint=f"/api/v1/properties/{property_id}/availability",
                params=params
            )
            return response.get("data", response) if isinstance(response, dict) else response
        except StreamlineAPIError:
            pass
        
        # Fall back to JSON-RPC
        response = await self._make_jsonrpc_request(
            "GetPropertyAvailability",
            {
                "unit_id": property_id,
                "startdate": start_date,
                "enddate": end_date
            }
        )
        
        return response.get("data", response) if isinstance(response, dict) else response
    
    async def get_rates(
        self,
        property_id: int,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get pricing/rates for a property within a date range
        
        Args:
            property_id: The Streamline property/unit ID
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            
        Returns:
            Rates data dictionary
        """
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        # Try REST API first
        try:
            response = await self._make_rest_request(
                endpoint=f"/api/v1/properties/{property_id}/rates",
                params=params
            )
            return response.get("data", response) if isinstance(response, dict) else response
        except StreamlineAPIError:
            pass
        
        # Fall back to JSON-RPC
        response = await self._make_jsonrpc_request(
            "GetPropertyRates",
            {
                "unit_id": property_id,
                "startdate": start_date,
                "enddate": end_date
            }
        )
        
        return response.get("data", response) if isinstance(response, dict) else response


# Singleton instance for easy import
def get_streamline_service() -> StreamlineService:
    """
    Factory function to get a StreamlineService instance
    
    Returns:
        StreamlineService instance configured from settings
    """
    return StreamlineService()

