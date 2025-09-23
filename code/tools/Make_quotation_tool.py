import os
import datetime
import statistics
import sys
from typing import List, Dict, Any
from groq import Groq
from pathlib import Path

# Add utils to path for secrets manager
current_dir = Path(__file__).parent
utils_dir = current_dir.parent / "utils"
sys.path.insert(0, str(utils_dir))

from secrets_manager import get_secret

# Load environment variables
GROQ_API_KEY = get_secret("GROQ_API_KEY", "groq")
GROQ_MODEL = get_secret("GROQ_MODEL", "groq")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

def ask_llm_for_daily_cost(destination: str, max_retries: int = 3) -> float:
    """
    Ask the LLM how much a traveler spends daily on food/attractions in a destination.
    Retry up to `max_retries` if the result is not a clean float.
    """
    query = f"Give me a single number: the average daily cost for a tourist in {destination} (food + attractions). Return only the number."

    for attempt in range(max_retries):
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that returns only numbers."},
                {"role": "user", "content": query},
            ],
        )
        result = response.choices[0].message.content.strip()

        # Try to parse a float
        try:
            daily_cost = float(result.split()[0].replace("$", "").replace(",", ""))
            return daily_cost
        except ValueError:
            if attempt < max_retries - 1:
                continue
            raise ValueError(f"LLM did not return a valid number after {max_retries} tries. Got: {result}")

from langchain.agents import tool

@tool
def make_quotation(
    hotel_prices: List[float],
    flight_prices: List[float],
    start_date: str,
    end_date: str,
    destination: str
) -> Dict[str, Any]:
    """
    Calculate total vacation cost given hotel/flight prices and destination.
    
    Args:
        hotel_prices: List of hotel prices per night (can be string or float)
        flight_prices: List of flight prices (round-trip, can be string or float)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        destination: Name of the destination city
        
    Returns:
        Dict containing cost breakdown including hotel, flights, daily expenses, and total with commission
    """
    # Ensure prices are floats
    try:
        hotel_prices = [float(price) if isinstance(price, str) else float(price) for price in hotel_prices]
        flight_prices = [float(price) if isinstance(price, str) else float(price) for price in flight_prices]
    except (ValueError, TypeError) as e:
        return {"error": f"Invalid price format: {str(e)}"}

    # 1. Number of days
    d1 = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    d2 = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    num_days = (d2 - d1).days

    # 2. Avg hotel per night * days
    avg_hotel_price = statistics.mean(hotel_prices)
    total_hotel = round((avg_hotel_price * num_days),2)

    # 3. Average flight price (already round-trip from API)
    avg_flight_price = statistics.mean(flight_prices)

    # 4. LLM daily spend
    daily_cost = ask_llm_for_daily_cost(destination)
    total_daily_spend = round((daily_cost * num_days), 2)

    # 5. Final sum before commission
    total_estimate = round((total_hotel + avg_flight_price + total_daily_spend), 2)
    
    # 6. Final quotation with 10% commission
    quotation = round((total_estimate * 1.1), 2)

    return {
        "days": num_days,
        "hotel_total": total_hotel,
        "flight_total": avg_flight_price,
        "daily_cost_estimate": daily_cost,
        "daily_total": total_daily_spend,
        "subtotal": total_estimate,
        "commission_rate": 0.1,
        "commission_amount": round((total_estimate * 0.1), 2),
        "final_quotation": quotation
    }


# ---------------- TEST ---------------- #
if __name__ == "__main__":
    fake_hotels = [120, 150, 130]  # per night
    fake_flights = [300, 350, 400]  # round trip
    start = "2025-07-01"
    end = "2025-07-08"
    destination = "Barcelona"

    result = make_quotation.invoke(
        input={
            "hotel_prices": fake_hotels,
            "flight_prices": fake_flights,
            "start_date": start,
            "end_date": end,
            "destination": destination,
        }
    )
    print("Vacation Cost Breakdown:", result)

    print('Final quotation with commission:', result['final_quotation'])