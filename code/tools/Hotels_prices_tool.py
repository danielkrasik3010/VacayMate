import json
import sys
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
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
from typing import Optional, List, Dict, Any
from pathlib import Path

# Add utils to path for secrets manager
current_dir = Path(__file__).parent
utils_dir = current_dir.parent / "utils"
sys.path.insert(0, str(utils_dir))

from secrets_manager import get_secret

# --- API Key setup ---
SERPAPI_API_KEY = get_secret("SERPAPI_API_KEY", "serpapi")

# --- Define the tool's input schema ---
class HotelSearchInput(BaseModel):
    query: str = Field(..., description="The city, region, or specific hotel to search for.")
    check_in_date: date = Field(..., description="The check-in date for the hotel stay. Format: YYYY-MM-DD.")
    check_out_date: date = Field(..., description="The check-out date for the hotel stay. Format: YYYY-MM-DD.")
    adults: Optional[int] = Field(2, description="The number of adults. Defaults to 2.")
    children: Optional[int] = Field(0, description="The number of children. Defaults to 0.")

def simplify_hotels(hotels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extracts valuable fields, parses numeric prices, formats addresses, and generates human-readable summaries."""
    simplified = []

    for h in hotels:
        # Skip None or invalid entries
        if not h or not isinstance(h, dict):
            simplified.append({
                "name": "Invalid Hotel Data",
                "price": {"per_night": "N/A", "per_night_value": None, "total": "N/A", "total_value": None},
                "address": {"formatted": "Address not available"},
                "rating": None,
                "hotel_class": None,
                "amenities": "N/A",
                "booking_link": "",
                "summary": "Invalid hotel data entry"
            })
            continue
            
        # Helper to parse numeric price
        def parse_price(price_str):
            if price_str:
                return float(price_str.replace('$','').replace(',',''))
            return None

        # Safely get price data
        rate_per_night = h.get("rate_per_night", {})
        total_rate = h.get("total_rate", {})
        
        price_per_night = rate_per_night.get("lowest") if isinstance(rate_per_night, dict) else None
        total_price = total_rate.get("lowest") if isinstance(total_rate, dict) else None

        price_per_night_val = parse_price(price_per_night)
        total_price_val = parse_price(total_price)

        # Address formatting - prioritize real address over GPS coordinates
        # Check multiple possible address fields from the API
        real_address = h.get("address", "")
        street_address = h.get("street", "")
        city_address = h.get("city", "")
        postal_code = h.get("postal_code", "")
        
        # Also check other common address fields
        location_address = h.get("location", "")
        vicinity = h.get("vicinity", "")
        formatted_address_api = h.get("formatted_address", "")
        
        # Try to build a proper address from components
        address_parts = []
        
        # First try the formatted address from API
        if formatted_address_api and formatted_address_api != "Central area":
            formatted_address = formatted_address_api
        elif real_address and real_address != "Central area":
            formatted_address = real_address
        elif vicinity and vicinity != "Central area":
            formatted_address = vicinity
        elif location_address and location_address != "Central area":
            formatted_address = location_address
        else:
            # Build from parts
            if street_address:
                address_parts.append(street_address)
            if city_address:
                address_parts.append(city_address)
            if postal_code:
                address_parts.append(postal_code)
            
            if address_parts:
                formatted_address = ", ".join(address_parts)
            else:
                # Fallback to GPS coordinates only if no address available
                gps = h.get("gps_coordinates", {})
                lat = gps.get("latitude")
                lon = gps.get("longitude")
                formatted_address = f"{lat}, {lon}" if lat and lon else "Address not available"

        rating = h.get("overall_rating")
        hotel_class = h.get("hotel_class")

        # Extract amenities
        amenities = h.get("amenities", [])
        amenities_text = ", ".join(amenities[:3]) if amenities else "N/A"  # Show top 3 amenities
        
        # Extract location/neighborhood info
        location_info = h.get("location", "")
        neighborhood = h.get("neighborhood", "")
        area_description = neighborhood or location_info or "Central area"
        
        # Extract booking link
        booking_link = h.get("link", "")
        
        # Build simplified hotel dict
        hotel = {
            "name": h.get("name"),
            "description": h.get("description"),
            "rating": round(rating, 1) if rating else None,
            "hotel_class": hotel_class,
            "price": {
                "per_night": price_per_night,
                "per_night_value": price_per_night_val,
                "total": total_price,
                "total_value": total_price_val
            },
            "address": {
                "formatted": formatted_address,
                "area": area_description,
                "coordinates": {
                    "latitude": h.get("gps_coordinates", {}).get("latitude"),
                    "longitude": h.get("gps_coordinates", {}).get("longitude")
                }
            },
            "amenities": amenities_text,
            "booking_link": booking_link,
            "check_in": h.get("check_in_time"),
            "check_out": h.get("check_out_time"),
        }

        # Human-readable summary
        summary_parts = [
            hotel["name"],
            f"({hotel_class})" if hotel_class else "",
            f"{hotel['rating']}★" if hotel["rating"] else "",
            f"From ${price_per_night_val}/night" if price_per_night_val else "",
            f"(total ${total_price_val})" if total_price_val else "",
            f"At {formatted_address}" if formatted_address != "N/A" else ""
        ]
        hotel["summary"] = " ".join([p for p in summary_parts if p])

        simplified.append(hotel)

    return simplified


# --- LangChain Tool ---
@tool(args_schema=HotelSearchInput)
def hotel_search(query: str, check_in_date: date, check_out_date: date, adults: int = 2, children: int = 0, sort_by: Optional[str] = None) -> dict:
    """
    Searches for hotels using Google Hotels (via SerpApi).
    Returns simplified JSON with key details + human-readable summaries.
    """
    params = {
        "engine": "google_hotels",
        "q": query,
        "check_in_date": check_in_date.strftime('%Y-%m-%d'),
        "check_out_date": check_out_date.strftime('%Y-%m-%d'),
        "adults": str(adults),
        "children": str(children),
        "currency": "USD",
        "gl": "us",
        "hl": "en",
        "api_key": SERPAPI_API_KEY,
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            return {"error": results["error"]}

        # Collect hotels from all possible keys
        raw_hotels = results.get("properties", []) + results.get("featured_hotels", []) + results.get("other_hotels", [])

        simplified_hotels = simplify_hotels(raw_hotels)

        return {
            "query": query,
            "check_in_date": check_in_date.isoformat(),
            "check_out_date": check_out_date.isoformat(),
            "total_found": len(raw_hotels),
            "hotels": simplified_hotels,
        }

    except Exception as e:
        return {"error": f"Failed to perform hotel search: {str(e)}"}


# --- Test the tool ---
if __name__ == "__main__":
    test_params = {
        "query": "Paris",
        "gl": "us",
        "hl": "en",
        'currency': "USD",
        "check_in_date": date(2025, 9, 20),
        "check_out_date": date(2025, 9, 25),
        "adults": 1,
        "children": 0,
    }

    result = hotel_search.invoke(test_params)
    print(json.dumps(result, indent=2))
