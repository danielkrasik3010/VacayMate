
from datetime import datetime, timedelta, date
import sys
from typing import Optional
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
from langchain.agents import tool
from pathlib import Path

# Add utils to path for secrets manager
current_dir = Path(__file__).parent
utils_dir = current_dir.parent / "utils"
sys.path.insert(0, str(utils_dir))

from secrets_manager import get_secret

# API keys are loaded from environment variables via .env file
SERPAPI_API_KEY = get_secret('SERPAPI_API_KEY', 'serpapi')


# ========================================================================
#  LOCAL EVENT FINDER (top 20 results)
# ========================================================================

@tool
def search_events(
    location: str,
    start_date: str,
    end_date: str,
    event_type: Optional[str] = None
) -> str:
    """
    Finds local events in a given location between start_date and end_date.
    Returns top 20 events with title, date, venue, and link.
    Optional: filter by event type (concert, sports, festival, etc.)
    """
    try:
        if GoogleSearch is None:
            return [
                {
                    "title": "Sample Event 1",
                    "formatted_date": "Sep 16 - 7:00 PM",
                    "venue": "Local Venue",
                    "link": "https://example.com/event1",
                    "description": "Sample event description"
                },
                {
                    "title": "Sample Event 2", 
                    "formatted_date": "Sep 18 - 8:00 PM",
                    "venue": "Another Venue",
                    "link": "https://example.com/event2",
                    "description": "Another sample event"
                }
            ]
        
        query = f"Events in {location}"
        if event_type:
            query += f" {event_type}"

        # Use proper SerpAPI parameters for Google Events
        params = {
            "engine": "google_events",
            "q": query,
            "htichips": "date:month",  # This month's events
            "gl": "us",  # Country code
            "hl": "en",  # Language
            "api_key": SERPAPI_API_KEY
        }
        results = GoogleSearch(params).get_dict().get("events_results", [])[:20]
        
        # Process results according to SerpAPI format
        simplified = []
        for r in results:
            event_data = {
                "title": r.get("title", ""),
                "date": r.get("date", {}),
                "address": r.get("address", []),
                "link": r.get("link", ""),
                "description": r.get("description", ""),
                "ticket_info": r.get("ticket_info", [])
            }
            
            # Extract date information
            date_info = event_data["date"]
            if isinstance(date_info, dict):
                start_date_str = date_info.get("start_date", "")
                when_str = date_info.get("when", "")
                event_data["formatted_date"] = f"{start_date_str} - {when_str}" if when_str else start_date_str
            else:
                event_data["formatted_date"] = str(date_info)
            
            # Extract venue from address
            if event_data["address"]:
                event_data["venue"] = event_data["address"][0] if isinstance(event_data["address"], list) else str(event_data["address"])
            else:
                event_data["venue"] = "Venue TBD"
            
            simplified.append(event_data)
        
        # Return first 15 events
        simplified = simplified[:15]
        return simplified
    except Exception as e:
        return [{"title": "Error", "description": f"Error with Local Event Finder: {e}", "venue": "N/A", "formatted_date": "N/A"}]



# ========================================================================
# 5. TESTING THE TOOLS
# ========================================================================

if __name__ == "__main__":
    today = date.today()
    next_week = today + timedelta(days=7)
    print("Testing Local Event Finder...")
    event_result = search_events.invoke({
        "location": "New York",
        "start_date": today.strftime("%Y-%m-%d"),
        "end_date": next_week.strftime("%Y-%m-%d"),
        "event_type": ""  # optional
    })
    print(event_result)
    print("\n---------------------------------------")

