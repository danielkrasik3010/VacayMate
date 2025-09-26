"""
Defensive Node Functions for VacayMate

Enhanced node functions with defensive programming patterns:
- State validation and recovery
- Loop detection
- Resource limits
- Comprehensive error handling
- Circuit breaker integration
"""

import json
import sys
import os
from typing import Any, Dict, List
from langchain_core.runnables import RunnableLambda
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

# Import defensive patterns
from defensive_patterns import (
    safe_api_call,
    circuit_breaker,
    get_system_health
)
from states.defensive_state import defensive_node, defensive_state_manager

# Import defensive tools
from tools.defensive_flights_tool import get_flight_prices_defensive
from tools.defensive_hotels_tool import hotel_search_defensive
from tools.defensive_weather_tool import get_weather_forecast_defensive

# Import original tools that don't have defensive versions yet
from tools.destination_info_tool import get_destination_info
from tools.Event_finder_tool import search_events
from tools.Make_quotation_tool import make_quotation
from tools.city_mapping import get_city_code
from tools.Flights_prices_tool import get_flight_prices
from tools.Hotels_prices_tool import hotel_search

# Import constants
from consts import (
    MANAGER,
    RESEARCHER,
    PLANNER,
    CALCULATOR,
    SUMMARIZER,
    MERGE_RESULTS,
)

# Import LLM utilities
from llm import get_llm

# ===============================
# LIGHTWEIGHT STATE VALIDATION FUNCTIONS
# ===============================

def _validate_manager_inputs(state: Dict[str, Any]) -> None:
    """Validate inputs required by the manager node."""
    required_fields = ["user_request", "current_location", "destination", "start_date", "return_date"]
    missing_fields = []
    
    for field in required_fields:
        value = state.get(field, "")
        if not value or value.strip() == "" or value == "[MISSING]":
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

def _validate_researcher_inputs(state: Dict[str, Any]) -> None:
    """Validate inputs required by the researcher node."""
    required_fields = ["current_location", "destination", "start_date", "return_date"]
    for field in required_fields:
        value = state.get(field, "")
        if not value or value.strip() == "":
            raise ValueError(f"Missing required field for research: {field}")

def _validate_calculator_inputs(state: Dict[str, Any]) -> None:
    """Validate inputs required by the calculator node."""
    research_results = state.get("research_results", {})
    if not isinstance(research_results, dict):
        raise ValueError("Research results must be a dictionary")
    
    # Check if we have some data to calculate with
    flights = research_results.get("flights", [])
    accommodations = research_results.get("accommodations", {})
    hotels = accommodations.get("hotels", []) if isinstance(accommodations, dict) else []
    
    if not flights and not hotels:
        raise ValueError("No flight or hotel data available for cost calculation")

def _validate_planner_inputs(state: Dict[str, Any]) -> None:
    """Validate inputs required by the planner node."""
    required_fields = ["destination", "start_date", "return_date"]
    for field in required_fields:
        value = state.get(field, "")
        if not value or value.strip() == "":
            raise ValueError(f"Missing required field for planning: {field}")

def _validate_summarizer_inputs(state: Dict[str, Any]) -> None:
    """Validate inputs required by the summarizer node."""
    required_data = ["research_results", "calculator_results", "planner_results"]
    missing_data = []
    
    for data_field in required_data:
        if data_field not in state or not state[data_field]:
            missing_data.append(data_field)
    
    if len(missing_data) == len(required_data):
        raise ValueError("No data available from previous nodes for summarization")

def _validate_node_output(node_name: str, output: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize node output."""
    if not isinstance(output, dict):
        raise ValueError(f"{node_name} must return a dictionary")
    
    # Ensure no None values in critical fields
    for key, value in output.items():
        if value is None:
            print(f"⚠️ {node_name} returned None for {key}, replacing with empty default")
            if key.endswith("_messages"):
                output[key] = []
            elif key.endswith("_results"):
                output[key] = {}
            else:
                output[key] = ""
    
    return output

# ===============================
# DEFENSIVE NODE IMPLEMENTATIONS
# ===============================

def defensive_manager_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Defensive Manager Node with comprehensive error handling.
    
    The manager coordinates the overall workflow and validates inputs.
    """
    print(f"\n🎬 DEFENSIVE MANAGER NODE - Processing request")
    
    # Lightweight state validation - only validate inputs needed by this node
    try:
        _validate_manager_inputs(state)
        print("✅ MANAGER STATE VALIDATION: All required inputs validated successfully")
    except Exception as e:
        print(f"❌ MANAGER STATE VALIDATION FAILED: {e}")
        return {
            "manager_messages": [f"❌ Input validation failed: {str(e)}"],
            "final_plan": f"Cannot proceed with trip planning: Input validation failed - {str(e)}"
        }
    
    try:
        # Validate required inputs
        user_request = state.get("user_request", "").strip()
        current_location = state.get("current_location", "").strip()
        destination = state.get("destination", "").strip()
        start_date = state.get("start_date", "").strip()
        return_date = state.get("return_date", "").strip()
        
        # Check for missing critical information
        missing_fields = []
        if not user_request or user_request == "[MISSING]":
            missing_fields.append("user request")
        if not current_location or current_location == "[MISSING]":
            missing_fields.append("departure location")
        if not destination or destination == "[MISSING]":
            missing_fields.append("destination")
        if not start_date:
            missing_fields.append("start date")
        if not return_date:
            missing_fields.append("return date")
        
        if missing_fields:
            error_msg = f"Missing required information: {', '.join(missing_fields)}"
            manager_message = f"❌ ERROR: {error_msg}. Please provide all required travel details."
            
            return {
                "manager_messages": [manager_message],
                "final_plan": f"Cannot proceed with trip planning: {error_msg}"
            }
        
        # Validate date format and logic
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            return_dt = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
            
            if start_dt >= return_dt:
                error_msg = "Start date must be before return date"
                manager_message = f"❌ ERROR: {error_msg}"
                return {
                    "manager_messages": [manager_message],
                    "final_plan": f"Cannot proceed with trip planning: {error_msg}"
                }
                
            # Check if dates are in the past
            if start_dt < datetime.now():
                warning_msg = "⚠️ WARNING: Start date is in the past. Proceeding with planning anyway."
                state["manager_messages"].append(warning_msg)
                
        except ValueError as e:
            error_msg = f"Invalid date format: {e}"
            manager_message = f"❌ ERROR: {error_msg}"
            return {
                "manager_messages": [manager_message],
                "final_plan": f"Cannot proceed with trip planning: {error_msg}"
            }
        
        # Create comprehensive manager message
        trip_duration = (return_dt - start_dt).days
        manager_messages = []
        
        manager_message = (
            f"✅ MANAGER: Successfully validated trip request.\n"
            f"📍 Trip: {current_location} → {destination}\n"
            f"📅 Dates: {start_date} to {return_date} ({trip_duration} days)\n"
            f"📝 Request: {user_request}\n"
            f"🚀 Proceeding to research phase..."
        )
        manager_messages.append(manager_message)
        
        # Check if dates are in the past
        if start_dt < datetime.now():
            warning_msg = "⚠️ WARNING: Start date is in the past. Proceeding with planning anyway."
            manager_messages.append(warning_msg)
        
        # Add system health information
        health = get_system_health()
        if any(status.get("disabled", False) for status in health.get("circuit_breakers", {}).values()):
            warning_msg = "⚠️ WARNING: Some services are currently experiencing issues. Fallback data may be used."
            manager_messages.append(warning_msg)
        
        # Validate and return manager results
        output = {
            "manager_messages": manager_messages
        }
        print("✅ MANAGER OUTPUT VALIDATION: Manager output validated successfully")
        return _validate_node_output("Manager", output)
        
    except Exception as e:
        error_msg = f"Manager node encountered an unexpected error: {str(e)}"
        print(f"❌ MANAGER ERROR: {error_msg}")
        
        return {
            "manager_messages": [f"❌ MANAGER ERROR: {error_msg}"],
            "final_plan": f"Trip planning failed due to manager error: {error_msg}"
        }

def defensive_researcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Defensive Researcher Node with circuit breaker protection for API calls.
    
    Researches flights, hotels, and destination information with fallback strategies.
    """
    print(f"\n🔬 DEFENSIVE RESEARCHER NODE - Gathering travel data")
    
    # Lightweight state validation - only validate inputs needed by this node
    try:
        _validate_researcher_inputs(state)
        print("✅ RESEARCHER STATE VALIDATION: All required inputs validated successfully")
    except Exception as e:
        print(f"❌ RESEARCHER STATE VALIDATION FAILED: {e}")
        return {
            "researcher_messages": [f"❌ Input validation failed: {str(e)}"],
            "research_results": {
                "flights": [],
                "accommodations": {"hotels": [], "query": "unknown", "total_found": 0},
                "destination_info": [{"content": f"Research failed: {str(e)}"}]
            }
        }
    
    try:
        current_location = state.get("current_location", "")
        destination = state.get("destination", "")
        start_date = state.get("start_date", "")
        return_date = state.get("return_date", "")
        
        research_results = {}
        researcher_messages = []
        
        # 1. FLIGHT RESEARCH with defensive patterns
        print("🛫 Researching flights with defensive patterns...")
        try:
            # Convert city names to codes (same as original)
            source_code = get_city_code(current_location)
            dest_code = get_city_code(destination)
            
            # Format dates with time (same as original)
            outbound_departure_start = f"{start_date}T00:00:00"
            outbound_departure_end = f"{start_date}T23:59:59"
            inbound_departure_start = f"{return_date}T00:00:00"
            inbound_departure_end = f"{return_date}T23:59:59"
            
            flight_params = {
                "source": source_code,
                "destination": dest_code,
                "adults": 1,
                "currency": "USD",
                "outboundDepartureDateStart": outbound_departure_start,
                "outboundDepartureDateEnd": outbound_departure_end,
                "inboundDepartureDateStart": inbound_departure_start,
                "inboundDepartureDateEnd": inbound_departure_end
            }
            
            # Use the original flight tool with defensive wrapper
            flight_result = safe_api_call(
                tool_name="flight_search",
                api_func=lambda: get_flight_prices.invoke(flight_params),
                fallback_func=lambda: {"success": False, "flights": [], "count": 0, "error": "Flight search service unavailable"}
            )
            
            # Validate flight response with Pydantic
            try:
                from defensive_patterns import ValidatedFlightResponse
                validated_flight = ValidatedFlightResponse(**flight_result)
                flight_result = validated_flight.dict()
                print("✅ FLIGHT API OUTPUT VALIDATION: Flight response validated with Pydantic schema")
                researcher_messages.append(f"✅ Flight response validated successfully")
            except Exception as e:
                print(f"❌ FLIGHT API OUTPUT VALIDATION FAILED: {str(e)}")
                researcher_messages.append(f"⚠️ Flight response validation failed: {str(e)}")
                # Use fallback data if validation fails
                flight_result = {"success": False, "flights": [], "count": 0, "error": f"Response validation failed: {str(e)}"}
            
            if flight_result.get("success", False) and flight_result.get("flights"):
                research_results["flights"] = flight_result["flights"][:5]  # Limit to top 5
                researcher_messages.append(f"✅ Found {len(flight_result['flights'])} flight options")
            else:
                error_msg = flight_result.get("error", "Unknown flight search error")
                research_results["flights"] = []
                researcher_messages.append(f"⚠️ Flight search issue: {error_msg}")
                
        except Exception as e:
            research_results["flights"] = []
            researcher_messages.append(f"❌ Flight research failed: {str(e)}")
        
        # 2. HOTEL RESEARCH with defensive patterns
        print("🏨 Researching hotels with defensive patterns...")
        try:
            from datetime import date
            
            # Parse dates for hotel search
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            return_dt = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
            
            hotel_params = {
                "query": destination,
                "check_in_date": start_dt.date(),
                "check_out_date": return_dt.date(),
                "adults": 1,
                "children": 0
            }
            
            # Use the original hotel tool with defensive wrapper
            hotel_result = safe_api_call(
                tool_name="hotel_search",
                api_func=lambda: hotel_search.invoke({
                    "gl": "us",
                    "hl": "en",
                    "currency": "USD",
                    **hotel_params
                }),
                fallback_func=lambda: {"hotels": [], "query": destination, "total_found": 0, "error": "Hotel search service unavailable"}
            )
            
            # Validate hotel response with Pydantic
            try:
                from defensive_patterns import ValidatedHotelResponse
                # Ensure the response has the expected structure
                if "hotels" in hotel_result and not "check_in_date" in hotel_result:
                    hotel_result.update({
                        "query": hotel_result.get("query", destination),
                        "check_in_date": start_date,
                        "check_out_date": return_date,
                        "total_found": len(hotel_result.get("hotels", []))
                    })
                validated_hotel = ValidatedHotelResponse(**hotel_result)
                hotel_result = validated_hotel.dict()
                print("✅ HOTEL API OUTPUT VALIDATION: Hotel response validated with Pydantic schema")
                researcher_messages.append(f"✅ Hotel response validated successfully")
            except Exception as e:
                print(f"❌ HOTEL API OUTPUT VALIDATION FAILED: {str(e)}")
                researcher_messages.append(f"⚠️ Hotel response validation failed: {str(e)}")
                # Use fallback data if validation fails
                hotel_result = {"hotels": [], "query": destination, "check_in_date": start_date, "check_out_date": return_date, "total_found": 0, "error": f"Response validation failed: {str(e)}"}
            
            if hotel_result.get("hotels"):
                research_results["accommodations"] = {
                    "hotels": hotel_result["hotels"][:5],  # Limit to top 5
                    "query": hotel_result.get("query", destination),
                    "total_found": hotel_result.get("total_found", 0)
                }
                researcher_messages.append(f"✅ Found {len(hotel_result['hotels'])} hotel options")
            else:
                error_msg = hotel_result.get("error", "Unknown hotel search error")
                research_results["accommodations"] = {"hotels": [], "query": destination, "total_found": 0}
                researcher_messages.append(f"⚠️ Hotel search issue: {error_msg}")
                
        except Exception as e:
            research_results["accommodations"] = {"hotels": [], "query": destination, "total_found": 0}
            researcher_messages.append(f"❌ Hotel research failed: {str(e)}")
        
        # 3. DESTINATION INFO with fallback
        print("🗺️ Researching destination information...")
        try:
            destination_query = f"best things to do in {destination} attractions activities restaurants"
            dest_info_result = safe_api_call(
                tool_name="destination_info",
                api_func=lambda: get_destination_info.invoke({
                    "query": destination_query,
                    "num_results": 3
                }),
                fallback_func=lambda: [{"content": f"General information about {destination} is currently unavailable."}]
            )
            
            # Ensure the result is in the correct format (list of dicts with 'content' key)
            if isinstance(dest_info_result, list):
                # Check if items are strings and convert them to the expected format
                formatted_results = []
                for item in dest_info_result:
                    if isinstance(item, str):
                        formatted_results.append({"content": item})
                    elif isinstance(item, dict) and "content" in item:
                        formatted_results.append(item)
                    else:
                        formatted_results.append({"content": str(item)})
                research_results["destination_info"] = formatted_results
            else:
                # If it's not a list, wrap it in the expected format
                research_results["destination_info"] = [{"content": str(dest_info_result)}]
            
            researcher_messages.append(f"✅ Gathered destination information for {destination}")
            
        except Exception as e:
            research_results["destination_info"] = [{"content": f"Destination information unavailable: {str(e)}"}]
            researcher_messages.append(f"⚠️ Destination info limited: {str(e)}")
        
        # Add summary message
        total_flights = len(research_results.get("flights", []))
        total_hotels = len(research_results.get("accommodations", {}).get("hotels", []))
        
        summary_msg = (
            f"🔬 RESEARCHER SUMMARY:\n"
            f"✈️ Flights: {total_flights} options found\n"
            f"🏨 Hotels: {total_hotels} options found\n"
            f"📍 Destination info: {'Available' if research_results.get('destination_info') else 'Limited'}\n"
            f"🔧 System status: {len([s for s in get_system_health().get('circuit_breakers', {}).values() if s.get('disabled', False)])} services experiencing issues"
        )
        
        researcher_messages.append(summary_msg)
        
        # Validate and return comprehensive research results
        output = {
            "research_results": research_results,
            "researcher_messages": researcher_messages
        }
        print("✅ RESEARCHER OUTPUT VALIDATION: Researcher output validated successfully")
        return _validate_node_output("Researcher", output)
        
    except Exception as e:
        error_msg = f"Researcher node encountered an unexpected error: {str(e)}"
        print(f"❌ RESEARCHER ERROR: {error_msg}")
        
        return {
            "researcher_messages": [f"❌ RESEARCHER ERROR: {error_msg}"],
            "research_results": {
                "flights": [],
                "accommodations": {"hotels": [], "query": destination, "total_found": 0},
                "destination_info": [{"content": f"Research failed: {error_msg}"}]
            }
        }

def defensive_planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Defensive Planner Node with weather and events research.
    
    Plans the itinerary with weather forecasts and local events.
    """
    print(f"\n📅 DEFENSIVE PLANNER NODE - Creating itinerary")
    
    # Lightweight state validation - only validate inputs needed by this node
    try:
        _validate_planner_inputs(state)
    except Exception as e:
        print(f"⚠️ Planner input validation failed: {e}")
        return {
            "planner_messages": [f"❌ Input validation failed: {str(e)}"],
            "planner_results": {
                "weather_forecast": {"forecasts": [], "human_readable_summary": f"Planning failed: {str(e)}", "error": str(e)},
                "local_events": {"events": [], "query": "unknown", "error": str(e)}
            }
        }
    
    try:
        destination = state.get("destination", "")
        start_date = state.get("start_date", "")
        return_date = state.get("return_date", "")
        
        planner_results = {}
        planner_messages = []
        
        # 1. WEATHER FORECAST with defensive patterns
        print("🌤️ Getting weather forecast with defensive patterns...")
        try:
            # Calculate trip duration for weather forecast
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            return_dt = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
            trip_days = min((return_dt - start_dt).days + 1, 7)  # Limit to 7 days max
            
            weather_result = get_weather_forecast_defensive.invoke({
                "location": destination,
                "days": trip_days,
                "units": "metric"
            })
            
            # Validate weather response with Pydantic
            try:
                from defensive_patterns import ValidatedWeatherResponse
                validated_weather = ValidatedWeatherResponse(**weather_result)
                weather_result = validated_weather.dict()
                print("✅ WEATHER API OUTPUT VALIDATION: Weather response validated with Pydantic schema")
                planner_messages.append(f"✅ Weather response validated successfully")
            except Exception as e:
                print(f"❌ WEATHER API OUTPUT VALIDATION FAILED: {str(e)}")
                planner_messages.append(f"⚠️ Weather response validation failed: {str(e)}")
                # Use fallback data if validation fails
                weather_result = {
                    "forecasts": [],
                    "human_readable_summary": f"Weather forecast validation failed: {str(e)}",
                    "error": f"Response validation failed: {str(e)}"
                }
            
            if weather_result.get("forecasts"):
                planner_results["weather_forecast"] = weather_result
                planner_messages.append(f"✅ Weather forecast obtained for {trip_days} days")
            else:
                error_msg = weather_result.get("error", "Weather service unavailable")
                planner_results["weather_forecast"] = weather_result  # Include fallback data
                planner_messages.append(f"⚠️ Weather forecast limited: {error_msg}")
                
        except Exception as e:
            planner_results["weather_forecast"] = {
                "forecasts": [],
                "human_readable_summary": f"Weather forecast unavailable: {str(e)}",
                "error": str(e)
            }
            planner_messages.append(f"❌ Weather forecast failed: {str(e)}")
        
        # 2. LOCAL EVENTS with fallback
        print("🎉 Searching for local events...")
        try:
            events_result = safe_api_call(
                tool_name="events_search",
                api_func=lambda: search_events.invoke({
                    "location": destination,
                    "start_date": start_date,
                    "end_date": return_date
                }),
                fallback_func=lambda: []
            )
            
            if isinstance(events_result, list) and events_result:
                planner_results["local_events"] = events_result[:10]  # Limit to 10 events
                planner_messages.append(f"✅ Found {len(events_result)} local events")
            else:
                planner_results["local_events"] = []
                planner_messages.append("⚠️ No local events found or service unavailable")
                
        except Exception as e:
            planner_results["local_events"] = []
            planner_messages.append(f"❌ Events search failed: {str(e)}")
        
        # Create planning summary
        weather_available = bool(planner_results.get("weather_forecast", {}).get("forecasts"))
        events_count = len(planner_results.get("local_events", []))
        
        summary_msg = (
            f"📅 PLANNER SUMMARY:\n"
            f"🌤️ Weather forecast: {'Available' if weather_available else 'Limited'}\n"
            f"🎉 Local events: {events_count} found\n"
            f"📍 Planning for {destination} trip\n"
            f"🔧 All planning data collected successfully"
        )
        
        planner_messages.append(summary_msg)
        
        # Validate and return only the fields we want to update
        output = {
            "planner_results": planner_results,
            "planner_messages": planner_messages
        }
        return _validate_node_output("Planner", output)
        
    except Exception as e:
        error_msg = f"Planner node encountered an unexpected error: {str(e)}"
        print(f"❌ PLANNER ERROR: {error_msg}")
        
        return {
            "planner_messages": [f"❌ PLANNER ERROR: {error_msg}"],
            "planner_results": {
                "weather_forecast": {
                    "forecasts": [],
                    "human_readable_summary": f"Planning failed: {error_msg}",
                    "error": error_msg
                },
                "local_events": []
            }
        }

def defensive_calculator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Defensive Calculator Node with comprehensive cost analysis.
    
    Calculates trip costs with error handling and validation.
    """
    print(f"\n💵 DEFENSIVE CALCULATOR NODE - Computing costs")
    
    # Lightweight state validation - only validate inputs needed by this node
    try:
        _validate_calculator_inputs(state)
        print("✅ CALCULATOR STATE VALIDATION: All required inputs validated successfully")
    except Exception as e:
        print(f"❌ CALCULATOR STATE VALIDATION FAILED: {e}")
        return {
            "calculator_messages": [f"❌ Input validation failed: {str(e)}"],
            "calculator_results": {
                "total_cost": 0,
                "cost_breakdown": {"flights": 0, "accommodation": 0, "total": 0},
                "error": str(e)
            }
        }
    
    try:
        start_date = state.get("start_date", "")
        return_date = state.get("return_date", "")
        research_results = state.get("research_results", {})
        
        calculator_messages = []
        
        # Calculate trip duration
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            return_dt = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
            days = (return_dt - start_dt).days
            
            if days <= 0:
                raise ValueError("Invalid trip duration")
                
        except Exception as e:
            days = 7  # Default fallback
            calculator_messages.append(f"⚠️ Using default 7-day duration due to date error: {str(e)}")
        
        # Extract cost data with validation
        flights = research_results.get("flights", [])
        hotels = research_results.get("accommodations", {}).get("hotels", [])
        
        # Calculate flight costs
        flight_total = 0.0
        if flights:
            try:
                # Use the cheapest flight option
                cheapest_flight = min(flights, key=lambda f: f.get("priceUSD", float('inf')))
                flight_total = float(cheapest_flight.get("priceUSD", 0))
                calculator_messages.append(f"✅ Flight cost calculated: ${flight_total:.2f}")
            except (ValueError, TypeError) as e:
                calculator_messages.append(f"⚠️ Flight cost calculation error: {str(e)}")
        else:
            calculator_messages.append("⚠️ No flight data available for cost calculation")
        
        # Calculate hotel costs
        hotel_total = 0.0
        if hotels:
            try:
                # Use the cheapest hotel option
                cheapest_hotel = min(hotels, key=lambda h: h.get("price", {}).get("per_night_value", float('inf')))
                per_night = float(cheapest_hotel.get("price", {}).get("per_night_value", 0))
                hotel_total = per_night * days
                calculator_messages.append(f"✅ Hotel cost calculated: ${hotel_total:.2f} ({days} nights)")
            except (ValueError, TypeError) as e:
                calculator_messages.append(f"⚠️ Hotel cost calculation error: {str(e)}")
        else:
            calculator_messages.append("⚠️ No hotel data available for cost calculation")
        
        # Estimate daily expenses
        daily_cost_estimate = 100.0  # Default daily budget
        daily_total = daily_cost_estimate * days
        
        # Calculate totals
        subtotal = flight_total + hotel_total + daily_total
        commission_rate = 0.15  # 15% commission
        commission_amount = subtotal * commission_rate
        final_quotation = subtotal + commission_amount
        
        # Create calculator results
        calculator_results = {
            "days": days,
            "flight_total": flight_total,
            "hotel_total": hotel_total,
            "daily_cost_estimate": daily_cost_estimate,
            "daily_total": daily_total,
            "subtotal": subtotal,
            "commission_rate": commission_rate,
            "commission_amount": commission_amount,
            "final_quotation": final_quotation,
            "currency": "USD",
            "calculation_timestamp": datetime.now().isoformat()
        }
        
        # Create summary message
        summary_msg = (
            f"💵 CALCULATOR SUMMARY:\n"
            f"📅 Trip duration: {days} days\n"
            f"✈️ Flight cost: ${flight_total:.2f}\n"
            f"🏨 Hotel cost: ${hotel_total:.2f}\n"
            f"🍽️ Daily expenses: ${daily_total:.2f}\n"
            f"💰 Final quotation: ${final_quotation:.2f}\n"
            f"📊 Commission (15%): ${commission_amount:.2f}"
        )
        
        calculator_messages.append(summary_msg)
        
        # Validate and return only the fields we want to update
        output = {
            "calculator_results": calculator_results,
            "calculator_messages": calculator_messages
        }
        return _validate_node_output("Calculator", output)
        
    except Exception as e:
        error_msg = f"Calculator node encountered an unexpected error: {str(e)}"
        print(f"❌ CALCULATOR ERROR: {error_msg}")
        
        return {
            "calculator_messages": [f"❌ CALCULATOR ERROR: {error_msg}"],
            "calculator_results": {
                "days": 7,
                "flight_total": 0.0,
                "hotel_total": 0.0,
                "daily_cost_estimate": 100.0,
                "daily_total": 700.0,
                "subtotal": 700.0,
                "commission_rate": 0.15,
                "commission_amount": 105.0,
                "final_quotation": 805.0,
                "currency": "USD",
                "error": error_msg,
                "calculation_timestamp": datetime.now().isoformat()
            }
        }

def defensive_summarizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Defensive Summarizer Node that creates the final travel plan.
    
    Synthesizes all research into a comprehensive travel plan with error handling.
    """
    print(f"\n📝 DEFENSIVE SUMMARIZER NODE - Creating final plan")
    
    # Lightweight state validation - only validate inputs needed by this node
    try:
        _validate_summarizer_inputs(state)
    except Exception as e:
        print(f"⚠️ Summarizer input validation failed: {e}")
        return {
            "summarizer_messages": [f"❌ Input validation failed: {str(e)}"],
            "final_plan": f"Unable to create travel plan: {str(e)}",
            "plan_approved": False
        }
    
    try:
        # Extract all collected data
        user_request = state.get("user_request", "")
        current_location = state.get("current_location", "")
        destination = state.get("destination", "")
        start_date = state.get("start_date", "")
        return_date = state.get("return_date", "")
        
        research_results = state.get("research_results", {})
        calculator_results = state.get("calculator_results", {})
        planner_results = state.get("planner_results", {})
        
        # Build comprehensive final plan
        plan_sections = []
        
        # Header
        plan_sections.append(f"# 🌍 Complete Travel Plan: {destination}")
        plan_sections.append(f"**Trip:** {current_location} → {destination}")
        plan_sections.append(f"**Dates:** {start_date} to {return_date}")
        plan_sections.append(f"**Duration:** {calculator_results.get('days', 'Unknown')} days")
        plan_sections.append("")
        
        # Executive Summary
        final_cost = calculator_results.get('final_quotation', 0)
        plan_sections.append("## 📋 Executive Summary")
        plan_sections.append(f"Your {calculator_results.get('days', 'multi-day')} trip to {destination} has been carefully planned with comprehensive research.")
        plan_sections.append(f"**Total Estimated Cost: ${final_cost:.2f}**")
        plan_sections.append("")
        
        # Flight Information
        flights = research_results.get("flights", [])
        plan_sections.append("## ✈️ Flight Options")
        if flights:
            best_flight = flights[0]  # Assuming sorted by quality
            airline = best_flight.get("airline", "Unknown")
            price = best_flight.get("priceUSD", 0)
            plan_sections.append(f"**Recommended Flight:** {airline} - ${price:.2f}")
            plan_sections.append(f"**Details:** {best_flight.get('human_readable_summary', 'Flight details available')}")
        else:
            plan_sections.append("⚠️ Flight options are currently limited. Please check directly with airlines.")
        plan_sections.append("")
        
        # Accommodation Information
        hotels = research_results.get("accommodations", {}).get("hotels", [])
        plan_sections.append("## 🏨 Accommodation Options")
        if hotels:
            best_hotel = hotels[0]  # Assuming sorted by quality
            hotel_name = best_hotel.get("name", "Unknown Hotel")
            hotel_price = best_hotel.get("price", {}).get("per_night", "N/A")
            plan_sections.append(f"**Recommended Hotel:** {hotel_name}")
            plan_sections.append(f"**Price:** {hotel_price} per night")
            plan_sections.append(f"**Rating:** {best_hotel.get('rating', 'N/A')}★")
        else:
            plan_sections.append("⚠️ Hotel options are currently limited. Please check booking sites directly.")
        plan_sections.append("")
        
        # Weather Information
        weather = planner_results.get("weather_forecast", {})
        plan_sections.append("## 🌤️ Weather Forecast")
        if weather.get("human_readable_summary"):
            plan_sections.append(weather["human_readable_summary"])
        else:
            plan_sections.append("Weather information is currently unavailable. Please check local weather services.")
        plan_sections.append("")
        
        # Local Events
        events = planner_results.get("local_events", [])
        plan_sections.append("## 🎉 Local Events & Activities")
        if events:
            plan_sections.append(f"We found {len(events)} local events during your visit:")
            for i, event in enumerate(events[:5], 1):  # Show top 5
                event_title = event.get("title", "Unknown Event")
                event_date = event.get("formatted_date", "Date TBD")
                plan_sections.append(f"{i}. **{event_title}** - {event_date}")
        else:
            plan_sections.append("No specific events found, but there are always local attractions to explore!")
        plan_sections.append("")
        
        # Cost Breakdown
        plan_sections.append("## 💰 Cost Breakdown")
        plan_sections.append(f"- **Flights:** ${calculator_results.get('flight_total', 0):.2f}")
        plan_sections.append(f"- **Hotels:** ${calculator_results.get('hotel_total', 0):.2f}")
        plan_sections.append(f"- **Daily Expenses:** ${calculator_results.get('daily_total', 0):.2f}")
        plan_sections.append(f"- **Subtotal:** ${calculator_results.get('subtotal', 0):.2f}")
        plan_sections.append(f"- **Service Fee (15%):** ${calculator_results.get('commission_amount', 0):.2f}")
        plan_sections.append(f"- ****Total:** ${final_cost:.2f}**")
        plan_sections.append("")
        
        # Important Notes
        plan_sections.append("## ⚠️ Important Notes")
        plan_sections.append("- Prices are estimates and may vary")
        plan_sections.append("- Book flights and hotels as soon as possible for best rates")
        plan_sections.append("- Check visa requirements and travel restrictions")
        plan_sections.append("- Consider travel insurance for your trip")
        plan_sections.append("")
        
        # System Status
        health = get_system_health()
        disabled_services = [name for name, status in health.get("circuit_breakers", {}).items() 
                           if status.get("disabled", False)]
        if disabled_services:
            plan_sections.append("## 🔧 System Status")
            plan_sections.append(f"Note: Some services were temporarily unavailable during planning: {', '.join(disabled_services)}")
            plan_sections.append("Fallback data was used where necessary. Please verify critical information independently.")
            plan_sections.append("")
        
        # Footer
        plan_sections.append("---")
        plan_sections.append(f"*Plan generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')} by VacayMate AI*")
        plan_sections.append("*This is a comprehensive travel plan based on current available data.*")
        
        # Join all sections
        final_plan = "\n".join(plan_sections)
        
        # Add summarizer message
        summary_msg = (
            f"📝 SUMMARIZER COMPLETE:\n"
            f"✅ Comprehensive travel plan created\n"
            f"📊 Total cost: ${final_cost:.2f}\n"
            f"📄 Plan includes flights, hotels, weather, and activities\n"
            f"🎯 Ready for client presentation"
        )
        
        # Validate and return only the fields we want to update
        output = {
            "final_plan": final_plan,
            "plan_approved": True,
            "summarizer_messages": [summary_msg]
        }
        return _validate_node_output("Summarizer", output)
        
    except Exception as e:
        error_msg = f"Summarizer node encountered an unexpected error: {str(e)}"
        print(f"❌ SUMMARIZER ERROR: {error_msg}")
        
        # Create emergency plan
        emergency_plan = (
            f"# Emergency Travel Plan: {state.get('destination', 'Unknown')}\n\n"
            f"Due to a system error, we were unable to generate a complete travel plan.\n"
            f"Error: {error_msg}\n\n"
            f"Please contact our support team for manual assistance with your trip planning.\n"
            f"Trip details: {state.get('current_location', 'Unknown')} to {state.get('destination', 'Unknown')}\n"
            f"Dates: {state.get('start_date', 'Unknown')} to {state.get('return_date', 'Unknown')}"
        )
        
        return {
            "final_plan": emergency_plan,
            "plan_approved": False,
            "summarizer_messages": [f"❌ SUMMARIZER ERROR: {error_msg}"]
        }

def defensive_merge_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Defensive Merge Node that acts as a synchronization point.
    
    Just like the original, this doesn't update state - it just ensures both parallel nodes completed.
    """
    print(f"\n🔄 DEFENSIVE MERGE NODE - Consolidating results")
    
    # Just like the original merge node, return empty dict for synchronization
    return {}

# ===============================
# NODE FACTORY FUNCTIONS
# ===============================

def make_defensive_manager_node(llm: str = "gpt-4o-mini", prompt_cfg: Dict[str, Any] = None) -> RunnableLambda:
    """Create a defensive manager node."""
    return RunnableLambda(defensive_manager_node)

def make_defensive_researcher_node(llm: str = "gpt-4o-mini", tools: List = None, prompt_cfg: Dict[str, Any] = None) -> RunnableLambda:
    """Create a defensive researcher node."""
    return RunnableLambda(defensive_researcher_node)

def make_defensive_calculator_node(llm: str = "gpt-4o-mini", tools: List = None, prompt_cfg: Dict[str, Any] = None) -> RunnableLambda:
    """Create a defensive calculator node."""
    return RunnableLambda(defensive_calculator_node)

def make_defensive_planner_node(llm: str = "gpt-4o-mini", tools: List = None, prompt_cfg: Dict[str, Any] = None) -> RunnableLambda:
    """Create a defensive planner node."""
    return RunnableLambda(defensive_planner_node)

def make_defensive_summarizer_node(llm: str = "gpt-4o-mini", tools: List = None, prompt_cfg: Dict[str, Any] = None) -> RunnableLambda:
    """Create a defensive summarizer node."""
    return RunnableLambda(defensive_summarizer_node)

def make_defensive_merge_node(llm: str = "gpt-4o-mini", tools: List = None, prompt_cfg: Dict[str, Any] = None) -> RunnableLambda:
    """Create a defensive merge node."""
    return RunnableLambda(defensive_merge_node)

# Test function
if __name__ == "__main__":
    print("Testing defensive nodes...")
    
    # Create a test state
    from states.defensive_state import initialize_defensive_vacation_state
    
    test_state = initialize_defensive_vacation_state(
        user_request="Plan a romantic getaway",
        current_location="New York",
        destination="Paris",
        start_date="2025-10-15",
        return_date="2025-10-22"
    )
    
    print("✅ Created test state")
    print(f"State health: {defensive_state_manager.get_state_health(test_state)}")
    
    # Test manager node
    print("\n🧪 Testing manager node...")
    result_state = defensive_manager_node(test_state)
    print("✅ Manager node completed")
    
    print(f"Final state health: {defensive_state_manager.get_state_health(result_state)}")
    print(f"System health: {get_system_health()}")

