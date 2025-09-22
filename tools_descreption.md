# VacayMate Tools Documentation

This document provides detailed descriptions of all tools available in the VacayMate system.

## Event_finder_tool.py

**Purpose**: This tool finds local events in a specific location using Google Events via SerpAPI. It helps agents discover what's happening in a destination for travel planning purposes.

**Function Name**: `search_events`

- **Input**:
  - location (string): The city or area to search for events.
  - start_date (string): The start date of the search period in 'YYYY-MM-DD' format.
  - end_date (string): The end date of the search period in 'YYYY-MM-DD' format.
  - event_type (string, optional): A category to filter the events, such as 'concert', 'sports', or 'festival'.

- **Output**:
  - A **list** containing up to 15 events. Each event is a dictionary with the following keys:
    - title: The name of the event.
    - formatted_date: The formatted date and time of the event.
    - venue: The name of the venue or location.
    - link: A URL for more information.
    - description: Event description.
    - address: Event address information.
    - ticket_info: Ticket availability information.
  - If an error occurs, returns a list with an error event entry.

## destination_info_tool.py

**Purpose**: This tool performs a two-step web search and extraction process using Tavily API to gather detailed information about a destination. It searches for relevant web pages and scrapes content from the most relevant ones.

**Function Name**: `get_destination_info`

- **Input**:
  - query (string): The search query to find information about the destination (e.g., 'best things to do in Paris').
  - num_results (integer, optional): The number of top results to extract content from. The default is 5.

- **Output**:
  - A **JSON string** containing an array of objects. Each object represents a web page and includes:
    - url: The URL of the page.
    - content: The full, extracted text content of the page.
    - error: Error message if content extraction failed for that URL.
  - If no relevant URLs are found, returns JSON with {"status": "no_relevant_urls_found"}.
  - If an error occurs, returns JSON with {"error": "error message"}.

## Flights_prices_tool.py

**Purpose**: This tool finds flight prices and itineraries for round-trip flights between specified cities using the Kiwi API. It provides detailed flight information including prices, durations, and booking links.

**Function Name**: `get_flight_prices`

- **Input**:
  - source (string): The departure city name (e.g., 'barcelona', 'tel aviv'). The tool automatically converts to proper API format.
  - destination (string): The arrival city name (e.g., 'sofia', 'paris'). The tool automatically converts to proper API format.
  - adults (integer): The number of adult passengers.
  - currency (string): The preferred currency for the prices (e.g., 'USD', 'EUR').
  - outboundDepartureDateStart (string): The earliest departure date for the outbound flight in 'YYYY-MM-DD' format (automatically normalized to ISO).
  - outboundDepartureDateEnd (string): The latest departure date for the outbound flight in 'YYYY-MM-DD' format (automatically normalized to ISO).
  - inboundDepartureDateStart (string): The earliest departure date for the inbound flight in 'YYYY-MM-DD' format (automatically normalized to ISO).
  - inboundDepartureDateEnd (string): The latest departure date for the inbound flight in 'YYYY-MM-DD' format (automatically normalized to ISO).

- **Output**:
  - A **dictionary** with the following structure:
    - success (boolean): Whether the API call was successful.
    - flights (list): List of flight itineraries (up to 10). Each flight includes:
      - id: Unique flight identifier.
      - priceUSD: The price in US dollars.
      - priceEUR: The price in euros.
      - durationOutbound: The duration of the outbound flight (e.g., "2h 30m").
      - durationInbound: The duration of the inbound flight (e.g., "2h 45m").
      - lastAvailableSeats: The number of seats left.
      - outbound: Detailed outbound flight information (carrier, flight number, times, airports).
      - inbound: Detailed inbound flight information (carrier, flight number, times, airports).
      - bookingUrl: Direct link to book the flight on Kiwi.com.
      - human_readable_summary: Brief, easy-to-read summary of the flight and cost.
      - airline, flightNumber, departureAirport, arrivalAirport, departureTime, arrivalTime: Additional display fields.
    - count (integer): Number of flights returned.
    - debug: Debug information including API status and formatted parameters.
  - If an error occurs, returns a dictionary with success: false and error message.

## Hotels_prices_tool.py

**Purpose**: This tool searches for hotels in a specified city or region using Google Hotels via SerpAPI. It provides detailed information about available hotels, including pricing, ratings, location, and human-readable summaries.

**Function Name**: `hotel_search`

- **Input**:
  - query (string): The city, region, or specific hotel name to search for.
  - check_in_date (date): The check-in date as a Python date object.
  - check_out_date (date): The check-out date as a Python date object.
  - adults (integer, optional): The number of adults for the booking. Defaults to 2.
  - children (integer, optional): The number of children. Defaults to 0.
  - sort_by (string, optional): A parameter to sort the results (e.g., 'PRICE_ASC').

- **Output**:
  - A **dictionary** containing search results with the following structure:
    - query: The original search query.
    - check_in_date: The check-in date in ISO format.
    - check_out_date: The check-out date in ISO format.
    - total_found: The total number of hotels found.
    - hotels: A list of simplified hotel objects. Each hotel contains:
      - name: The hotel's name.
      - description: A brief description.
      - rating: The overall rating (rounded to 1 decimal).
      - hotel_class: A star rating (e.g., "5-star").
      - price: Nested object with per_night, per_night_value, total, total_value.
      - address: Nested object with formatted address, area, and coordinates.
      - amenities: Top 3 amenities as comma-separated string.
      - booking_link: Direct link to book the hotel.
      - check_in: Check-in time.
      - check_out: Check-out time.
      - summary: Human-readable summary with name, rating, price, and location.
  - If an error occurs, returns a dictionary with {"error": "error message"}.

## Weather_Forecast_tool.py

**Purpose**: This tool retrieves the daily weather forecast for a given location using OpenWeatherMap API. It provides key weather metrics and a human-readable summary for vacation planning.

**Function Name**: `get_weather_forecast`

- **Input**:
  - location (string): The city or location to get the weather forecast for.
  - days (integer, optional): The number of days for the forecast. Defaults to 5.
  - units (string, optional): The unit system for temperature. 'metric' (Celsius) or 'imperial' (Fahrenheit). Defaults to 'metric'.

- **Output**:
  - A **dictionary** with the following structure:
    - forecasts: A list of dictionaries, where each dictionary contains:
      - date: The date of the forecast (YYYY-MM-DD format).
      - condition: A detailed description of the weather (e.g., 'light rain', 'clear sky').
      - temp_high: The highest temperature for the day.
      - temp_low: The lowest temperature for the day.
      - wind_speed: The wind speed.
      - humidity: The humidity percentage.
      - precipitation: The amount of precipitation.
    - human_readable_summary: A combined text summary of the forecast for all the requested days.
  - If an error occurs, returns a dictionary with empty forecasts list and error message in the summary.

## Make_quotation_tool.py

**Purpose**: This tool calculates a total estimated vacation cost by combining hotel costs, flight costs, and estimated daily expenses. It uses a Groq LLM to estimate daily spending on food and attractions for the specific destination. The output includes a detailed cost breakdown with a 10% commission added.

**Function Name**: `make_quotation`

- **Input**:
  - hotel_prices (List[float]): A list of hotel prices per night.
  - flight_prices (List[float]): A list of round-trip flight prices.
  - start_date (string): The start date of the vacation in 'YYYY-MM-DD' format.
  - end_date (string): The end date of the vacation in 'YYYY-MM-DD' format.
  - destination (string): The destination city or location of the vacation.

- **Output**:
  - A **dictionary** containing a detailed cost breakdown with the following keys:
    - days: The total number of days of the vacation.
    - hotel_total: The total estimated cost of hotels for the duration of the trip.
    - flight_total: The average price of the flights (round-trip).
    - daily_cost_estimate: The estimated daily cost per person for food and attractions, provided by the LLM.
    - daily_total: The total estimated cost for food and attractions for the entire trip.
    - subtotal: The sum of hotel_total, flight_total, and daily_total.
    - commission_rate: The commission rate applied (0.1 = 10%).
    - commission_amount: The commission amount in currency.
    - final_quotation: The final quoted price including 10% commission.
  - If an error occurs (e.g., invalid price format), returns a dictionary with {"error": "error message"}.

## Tool Usage by Agents

The VacayMate system uses different tools across its specialized agents:

### Researcher Agent
Uses 3 tools to gather raw vacation data:
1. `destination_info_tool.py` - Gets destination information and attractions
2. `Flights_prices_tool.py` - Searches for flight options and prices  
3. `Hotels_prices_tool.py` - Searches for hotel availability and pricing

### Planner Agent  
Uses 2 tools to create itineraries:
1. `Weather_Forecast_tool.py` - Gets weather forecasts for trip planning
2. `Event_finder_tool.py` - Finds local events and activities

### Calculator Agent
Uses 1 tool for cost estimation:
1. `Make_quotation_tool.py` - Calculates total vacation costs with breakdown

### Manager Agent
The manager agent coordinates all other agents but does not use tools directly. It orchestrates the workflow and manages data transfer between agents.

### Summarizer Agent
The summarizer agent does not use tools directly. It combines outputs from the Calculator and Planner agents to create the final vacation plan presentation.

---

This document serves as the single source of truth for all VacayMate tool documentation. Each tool description includes the correct function name, accurate input/output specifications, and reflects the current implementation in the codebase.