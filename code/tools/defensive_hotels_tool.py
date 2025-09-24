"""
Defensive Hotel Search Tool

Enhanced version of the hotel search tool with defensive programming patterns:
- Circuit breaker protection
- Exponential backoff retry logic
- Output validation with Pydantic
- Resource limits
- Comprehensive error handling
"""

import os
import json
import sys
from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

# Import defensive patterns
from defensive_patterns import (
    safe_api_call, 
    hotel_fallback, 
    ValidatedHotelResponse,
    retry_with_backoff,
    resource_limited
)

# Add utils to path for secrets manager
utils_dir = current_dir.parent / "utils"
sys.path.insert(0, str(utils_dir))

from secrets_manager import get_secret

# Import SerpAPI with fallback
try:
    from serpapi import GoogleSearch
except ImportError:
    try:
        from serpapi.google_search import GoogleSearch
    except ImportError:
        try:
            from serpapi.serp_api_client import GoogleSearch
        except ImportError:
            # Fallback - define a dummy class to prevent import errors
            class GoogleSearch:
                def __init__(self, *args, **kwargs):
                    pass
                def get_dict(self):
                    return {"error": "SerpAPI not available"}
            print("Warning: SerpAPI GoogleSearch not available, using fallback")

# Import original hotel tool functions
from tools.Hotels_prices_tool import simplify_hotels

SERPAPI_API_KEY = get_secret("SERPAPI_API_KEY", "serpapi")

# Define the tool's input schema
class HotelSearchInput(BaseModel):
    query: str = Field(..., description="The city, region, or specific hotel to search for.")
    check_in_date: date = Field(..., description="The check-in date for the hotel stay. Format: YYYY-MM-DD.")
    check_out_date: date = Field(..., description="The check-out date for the hotel stay. Format: YYYY-MM-DD.")
    adults: Optional[int] = Field(2, description="The number of adults. Defaults to 2.")
    children: Optional[int] = Field(0, description="The number of children. Defaults to 0.")

@resource_limited(max_memory_mb=150, max_time_seconds=40)
@retry_with_backoff(max_retries=3, base_delay=1.5)
def _fetch_hotel_data(query: str, check_in_date: date, check_out_date: date, 
                     adults: int = 2, children: int = 0) -> Dict[str, Any]:
    """
    Internal function to fetch hotel data with defensive patterns.
    
    This function is wrapped with resource limits and retry logic.
    """
    # Validate inputs
    if not query or not query.strip():
        raise ValueError("Query parameter is required and cannot be empty")
    
    if check_in_date >= check_out_date:
        raise ValueError("Check-in date must be before check-out date")
    
    if adults < 1 or adults > 10:
        raise ValueError("Adults must be between 1 and 10")
    
    if children < 0 or children > 10:
        raise ValueError("Children must be between 0 and 10")
    
    # Prepare API parameters
    params = {
        "engine": "google_hotels",
        "q": query.strip(),
        "check_in_date": check_in_date.strftime('%Y-%m-%d'),
        "check_out_date": check_out_date.strftime('%Y-%m-%d'),
        "adults": str(adults),
        "children": str(children),
        "currency": "USD",
        "gl": "us",
        "hl": "en",
        "api_key": SERPAPI_API_KEY,
    }
    
    # Validate API key
    if not SERPAPI_API_KEY or SERPAPI_API_KEY == "your_serpapi_key_here":
        raise ValueError("SERPAPI_API_KEY is not properly configured")
    
    # Make the API call
    search = GoogleSearch(params)
    results = search.get_dict()
    
    # Check for API errors
    if "error" in results:
        error_msg = results["error"]
        if "Invalid API key" in error_msg:
            raise ValueError(f"Invalid SERPAPI API key: {error_msg}")
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            raise Exception(f"API quota exceeded: {error_msg}")
        else:
            raise Exception(f"API error: {error_msg}")
    
    # Collect hotels from all possible keys
    raw_hotels = (
        results.get("properties", []) + 
        results.get("featured_hotels", []) + 
        results.get("other_hotels", [])
    )
    
    # Validate that we got some data
    if not raw_hotels:
        # Check if there are any results at all
        if not any(key in results for key in ["properties", "featured_hotels", "other_hotels"]):
            raise Exception("No hotel data found in API response")
    
    # Process the hotels
    simplified_hotels = simplify_hotels(raw_hotels)
    
    return {
        "query": query,
        "check_in_date": check_in_date.isoformat(),
        "check_out_date": check_out_date.isoformat(),
        "total_found": len(raw_hotels),
        "hotels": simplified_hotels,
        "debug": {
            "raw_hotel_count": len(raw_hotels),
            "api_response_keys": list(results.keys()),
            "timestamp": date.today().isoformat()
        }
    }

@tool(args_schema=HotelSearchInput)
def hotel_search_defensive(query: str, check_in_date: date, check_out_date: date, 
                          adults: int = 2, children: int = 0, 
                          sort_by: Optional[str] = None) -> Dict[str, Any]:
    """
    Defensive hotel search tool with circuit breaker, retry logic, and validation.
    
    This tool automatically handles:
    - API failures with exponential backoff
    - Circuit breaker protection against repeated failures
    - Input validation and sanitization
    - Output validation with Pydantic models
    - Resource usage limits
    - Comprehensive error logging
    
    Args:
        query: The city, region, or specific hotel to search for
        check_in_date: Check-in date (YYYY-MM-DD format)
        check_out_date: Check-out date (YYYY-MM-DD format)
        adults: Number of adults (1-10, defaults to 2)
        children: Number of children (0-10, defaults to 0)
        sort_by: Optional sorting parameter (not used in current implementation)
    
    Returns:
        Dict: Validated hotel search results with fallback data if needed
    """
    def hotel_api_call():
        return _fetch_hotel_data(
            query=query,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=adults,
            children=children
        )
    
    def enhanced_fallback():
        return hotel_fallback(
            query=query,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=adults,
            children=children
        )
    
    # Use safe API call with circuit breaker protection
    result = safe_api_call(
        tool_name="hotel_search",
        api_func=hotel_api_call,
        fallback_func=enhanced_fallback
    )
    
    # Validate the result using Pydantic
    try:
        validated_result = ValidatedHotelResponse(**result)
        return validated_result.dict()
    except Exception as e:
        # If validation fails, return a safe fallback
        return ValidatedHotelResponse(
            query=query,
            check_in_date=check_in_date.isoformat(),
            check_out_date=check_out_date.isoformat(),
            total_found=0,
            hotels=[],
            error=f"Response validation failed: {str(e)}"
        ).dict()

# Backward compatibility - alias to the original function name
hotel_search = hotel_search_defensive

# Test function
if __name__ == "__main__":
    # Test the defensive hotel tool
    test_params = {
        "query": "Paris",
        "check_in_date": date(2025, 9, 20),
        "check_out_date": date(2025, 9, 25),
        "adults": 1,
        "children": 0,
    }
    
    print("Testing defensive hotel search tool...")
    result = hotel_search_defensive.invoke(test_params)
    
    print(json.dumps(result, indent=2, default=str))
    
    # Test circuit breaker status
    from defensive_patterns import get_system_health
    print("\nSystem health:", json.dumps(get_system_health(), indent=2, default=str))

