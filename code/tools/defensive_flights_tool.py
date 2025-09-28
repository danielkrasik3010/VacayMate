"""
Defensive Flight Search Tool

Enhanced version of the flight search tool with defensive programming patterns:
- Circuit breaker protection
- Exponential backoff retry logic
- Output validation with Pydantic
- Resource limits
- Comprehensive error handling
"""

from langchain.agents import tool
import requests
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

# Import defensive patterns
from defensive_patterns import (
    safe_api_call, 
    flight_fallback, 
    ValidatedFlightResponse,
    retry_with_backoff,
    resource_limited
)

# Add utils to path for secrets manager
utils_dir = current_dir.parent / "utils"
sys.path.insert(0, str(utils_dir))

from secrets_manager import get_secret

# Import original flight tool functions
from tools.Flights_prices_tool import (
    CITY_CODES, 
    create_city_mapping, 
    get_city_code, 
    simplify_itineraries,
    minutes_to_hm
)

FLIGHTS_RAPID_API_KEY = get_secret("FLIGHTS_RAPID_API_KEY", "flights")

@resource_limited(max_memory_mb=200, max_time_seconds=45)
@retry_with_backoff(max_retries=3, base_delay=2.0)
def _fetch_flight_data(source: str, destination: str, adults: int, currency: str,
                      outboundDepartureDateStart: str, outboundDepartureDateEnd: str,
                      inboundDepartureDateStart: str, inboundDepartureDateEnd: str) -> Dict[str, Any]:
    """
    Internal function to fetch flight data with defensive patterns.
    
    This function is wrapped with resource limits and retry logic.
    """
    import re
    
    # Normalize dates to full ISO format
    def normalize_date(date_str: str, is_start=True) -> str:
        """Convert YYYY-MM-DD to full ISO datetime."""
        if "T" in date_str:  # already full ISO
            return date_str
        return f"{date_str}T00:00:00" if is_start else f"{date_str}T23:59:59"

    # Normalize all dates
    outboundDepartureDateStart = normalize_date(outboundDepartureDateStart, True)
    outboundDepartureDateEnd = normalize_date(outboundDepartureDateEnd, False)
    inboundDepartureDateStart = normalize_date(inboundDepartureDateStart, True)
    inboundDepartureDateEnd = normalize_date(inboundDepartureDateEnd, False)

    # Format city codes with validation
    def format_city_code(city_str):
        if isinstance(city_str, str) and city_str.startswith('City:'):
            return city_str
        city_str = str(city_str).strip().lower()
        for code in CITY_CODES:
            if city_str in code.lower():
                return code
        parts = re.split(r'[,_-]', city_str)
        if len(parts) >= 2:
            return f'City:{parts[0]}_{parts[-1][:2]}'
        return f'City:{city_str}'

    # Format and validate inputs
    source = format_city_code(source)
    destination = format_city_code(destination)
    
    # Validate required parameters
    if not source or not destination:
        raise ValueError("Source and destination cities are required")
    
    if adults < 1 or adults > 9:
        raise ValueError("Adults must be between 1 and 9")

    url = "https://kiwi-com-cheap-flights.p.rapidapi.com/round-trip"
    querystring = {
        "source": source,
        "destination": destination,
        "currency": currency.lower(),
        "locale": "en",
        "adults": str(adults),
        "children": "0",
        "infants": "0",
        "handbags": "1",
        "holdbags": "0",
        "cabinClass": "ECONOMY",
        "sortBy": "QUALITY",
        "sortOrder": "ASCENDING",
        "applyMixedClasses": "true",
        "allowReturnFromDifferentCity": "true",
        "allowChangeInboundDestination": "true",
        "allowChangeInboundSource": "true",
        "allowDifferentStationConnection": "true",
        "enableSelfTransfer": "true",
        "allowOvernightStopover": "true",
        "enableTrueHiddenCity": "true",
        "enableThrowAwayTicketing": "true",
        "outbound": "SUNDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY,MONDAY,TUESDAY",
        "transportTypes": "FLIGHT",
        "contentProviders": "FLIXBUS_DIRECTS,FRESH,KAYAK,KIWI",
        "limit": "10",
        "outboundDepartureDateStart": outboundDepartureDateStart,
        "outboundDepartureDateEnd": outboundDepartureDateEnd,
        "inboundDepartureDateStart": inboundDepartureDateStart,
        "inboundDepartureDateEnd": inboundDepartureDateEnd,
    }
    
    headers = {
        "x-rapidapi-key": FLIGHTS_RAPID_API_KEY,
        "x-rapidapi-host": "kiwi-com-cheap-flights.p.rapidapi.com"
    }

    # Make the API request with timeout
    response = requests.get(url, headers=headers, params=querystring, timeout=30)
    
    # Check for HTTP errors
    if response.status_code == 429:
        raise requests.RequestException(f"Rate limited by API (status {response.status_code})")
    elif response.status_code >= 500:
        raise requests.RequestException(f"Server error (status {response.status_code})")
    elif response.status_code != 200:
        raise requests.RequestException(f"API returned status {response.status_code}")

    # Parse JSON response
    try:
        raw_json = response.json()
    except ValueError as e:
        raise requests.RequestException(f"Invalid JSON response: {e}")
    
    # Process and simplify the response
    simplified = simplify_itineraries(raw_json)
    flights = simplified.get("itineraries", [])
    
    return {
        "success": True,
        "flights": flights,
        "count": len(flights),
        "debug": {
            "status_code": response.status_code,
            "source_formatted": source,
            "destination_formatted": destination,
            "raw_response_keys": list(raw_json.keys()) if isinstance(raw_json, dict) else [],
            "timestamp": datetime.now().isoformat()
        },
    }

@tool
def get_flight_prices_defensive(
    source: str,
    destination: str,
    adults: int,
    currency: str,
    outboundDepartureDateStart: str,
    outboundDepartureDateEnd: str,
    inboundDepartureDateStart: str,
    inboundDepartureDateEnd: str
) -> Dict[str, Any]:
    """
    Defensive flight search tool with circuit breaker, retry logic, and validation.
    
    This tool automatically handles:
    - API failures with exponential backoff
    - Circuit breaker protection against repeated failures
    - Input validation and sanitization
    - Output validation with Pydantic models
    - Resource usage limits
    - Comprehensive error logging
    
    Args:
        source: Source city name
        destination: Destination city name
        adults: Number of adult passengers (1-9)
        currency: Currency code (e.g., 'USD', 'EUR')
        outboundDepartureDateStart: Outbound departure date start (YYYY-MM-DD)
        outboundDepartureDateEnd: Outbound departure date end (YYYY-MM-DD)
        inboundDepartureDateStart: Inbound departure date start (YYYY-MM-DD)
        inboundDepartureDateEnd: Inbound departure date end (YYYY-MM-DD)
    
    Returns:
        Dict: Validated flight search results with fallback data if needed
    """
    def flight_api_call():
        return _fetch_flight_data(
            source=source,
            destination=destination,
            adults=adults,
            currency=currency,
            outboundDepartureDateStart=outboundDepartureDateStart,
            outboundDepartureDateEnd=outboundDepartureDateEnd,
            inboundDepartureDateStart=inboundDepartureDateStart,
            inboundDepartureDateEnd=inboundDepartureDateEnd
        )
    
    def enhanced_fallback():
        return flight_fallback(
            source=source,
            destination=destination,
            adults=adults,
            currency=currency,
            outboundDepartureDateStart=outboundDepartureDateStart,
            outboundDepartureDateEnd=outboundDepartureDateEnd,
            inboundDepartureDateStart=inboundDepartureDateStart,
            inboundDepartureDateEnd=inboundDepartureDateEnd
        )
    
    # Use safe API call with circuit breaker protection
    result = safe_api_call(
        tool_name="flight_search",
        api_func=flight_api_call,
        fallback_func=enhanced_fallback
    )
    
    # Validate the result using Pydantic
    try:
        validated_result = ValidatedFlightResponse(**result)
        return validated_result.dict()
    except Exception as e:
        # If validation fails, return a safe fallback
        return ValidatedFlightResponse(
            success=False,
            flights=[],
            count=0,
            error=f"Response validation failed: {str(e)}"
        ).dict()

# Backward compatibility - alias to the original function name
get_flight_prices = get_flight_prices_defensive

# Test function
if __name__ == "__main__":
    # Test the defensive flight tool
    test_params = {
        "source": "barcelona",
        "destination": "paris",
        "adults": 1,
        "currency": "USD",
        "outboundDepartureDateStart": "2025-09-15",
        "outboundDepartureDateEnd": "2025-09-15",
        "inboundDepartureDateStart": "2025-09-20",
        "inboundDepartureDateEnd": "2025-09-20"
    }
    
    print("Testing defensive flight search tool...")
    result = get_flight_prices_defensive.invoke(test_params)
    
    import json
    print(json.dumps(result, indent=2))
    
    # Test circuit breaker status
    from defensive_patterns import get_system_health
    print("\nSystem health:", json.dumps(get_system_health(), indent=2))

