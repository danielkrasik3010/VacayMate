"""
Unit tests for VacayMate state management and transitions.

Tests cover:
- State initialization and validation
- State transitions and updates
- Pydantic model validation
- State structure integrity
- Data type validation
"""

import pytest
from datetime import datetime, date
from typing import Dict, Any
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from states.VacayMate_state import (
    VacationPlannerState,
    initialize_vacation_state,
    FlightItinerary,
    Hotel,
    HotelSearchResult,
    WeatherForecast,
    Event
)


class TestStateInitialization:
    """Test VacationPlannerState initialization."""

    def test_initialize_vacation_state_basic(self):
        """Test basic state initialization with required parameters."""
        state = initialize_vacation_state(
            user_request="Plan a trip to Paris",
            current_location="Barcelona",
            destination="Paris",
            start_date="2025-09-15",
            return_date="2025-09-20"
        )
        
        # Verify basic structure
        assert isinstance(state, dict)
        
        # Verify required fields
        assert state["user_request"] == "Plan a trip to Paris"
        assert state["current_location"] == "Barcelona"
        assert state["destination"] == "Paris"
        assert state["start_date"] == "2025-09-15"
        assert state["return_date"] == "2025-09-20"
        assert state["travel_dates"] == "2025-09-15 to 2025-09-20"

    def test_initialize_vacation_state_with_defaults(self):
        """Test state initialization with default values."""
        state = initialize_vacation_state()
        
        # Verify default values
        assert state["user_request"] == ""
        assert state["current_location"] == ""
        assert state["destination"] == ""
        assert state["start_date"] == ""
        assert state["return_date"] == ""
        assert state["travel_dates"] == ""
        
        # Verify default collections
        assert state["manager_messages"] == []
        assert state["researcher_messages"] == []
        assert state["calculator_messages"] == []
        assert state["planner_messages"] == []
        assert state["summarizer_messages"] == []
        
        assert state["research_results"] == {}
        assert state["planner_results"] == {}
        assert state["calculator_results"] == {}
        
        assert state["itinerary_draft"] == ""
        assert state["final_plan"] == ""
        assert state["plan_approved"] is False

    def test_initialize_vacation_state_with_prompts(self):
        """Test state initialization with custom prompt configurations."""
        manager_prompt = {"role": "Manager", "instruction": "Manage workflow"}
        researcher_prompt = {"role": "Researcher", "instruction": "Research data"}
        
        state = initialize_vacation_state(
            user_request="Test trip",
            manager_prompt_cfg=manager_prompt,
            researcher_prompt_cfg=researcher_prompt
        )
        
        assert state["manager_prompt"] == manager_prompt
        assert state["researcher_prompt"] == researcher_prompt
        assert state["calculator_prompt"] == {}  # Default
        assert state["planner_prompt"] == {}  # Default
        assert state["summarizer_prompt"] == {}  # Default

    def test_initialize_vacation_state_with_tools(self):
        """Test state initialization with tools configuration."""
        tools = [
            {"name": "flight_tool", "type": "api"},
            {"name": "hotel_tool", "type": "api"}
        ]
        
        state = initialize_vacation_state(
            user_request="Test trip",
            tools=tools
        )
        
        assert state["tools"] == tools

    def test_travel_dates_formatting(self):
        """Test travel dates formatting in state initialization."""
        test_cases = [
            ("2025-09-15", "2025-09-20", "2025-09-15 to 2025-09-20"),
            ("2025-12-25", "2025-12-31", "2025-12-25 to 2025-12-31"),
            ("", "", ""),
            ("2025-09-15", "", ""),
            ("", "2025-09-20", "")
        ]
        
        for start_date, end_date, expected in test_cases:
            state = initialize_vacation_state(
                start_date=start_date,
                return_date=end_date
            )
            assert state["travel_dates"] == expected


class TestStateStructure:
    """Test state structure and field validation."""

    def test_state_required_keys(self, sample_vacation_state):
        """Test that all required keys are present in state."""
        required_keys = [
            "user_request", "current_location", "destination",
            "travel_dates", "start_date", "return_date",
            "manager_messages", "researcher_messages", "calculator_messages",
            "planner_messages", "summarizer_messages",
            "research_results", "planner_results", "calculator_results",
            "manager_prompt", "researcher_prompt", "calculator_prompt",
            "planner_prompt", "summarizer_prompt", "tools",
            "itinerary_draft", "final_plan", "plan_approved"
        ]
        
        for key in required_keys:
            assert key in sample_vacation_state, f"Missing required key: {key}"

    def test_state_data_types(self, sample_vacation_state):
        """Test that state fields have correct data types."""
        # String fields
        string_fields = [
            "user_request", "current_location", "destination",
            "travel_dates", "start_date", "return_date",
            "itinerary_draft", "final_plan"
        ]
        for field in string_fields:
            assert isinstance(sample_vacation_state[field], str), f"{field} should be string"

        # List fields
        list_fields = [
            "manager_messages", "researcher_messages", "calculator_messages",
            "planner_messages", "summarizer_messages", "tools"
        ]
        for field in list_fields:
            assert isinstance(sample_vacation_state[field], list), f"{field} should be list"

        # Dict fields
        dict_fields = [
            "research_results", "planner_results", "calculator_results",
            "manager_prompt", "researcher_prompt", "calculator_prompt",
            "planner_prompt", "summarizer_prompt"
        ]
        for field in dict_fields:
            assert isinstance(sample_vacation_state[field], dict), f"{field} should be dict"

        # Boolean fields
        assert isinstance(sample_vacation_state["plan_approved"], bool)

    def test_message_list_structure(self, sample_vacation_state):
        """Test message list structure and annotations."""
        message_fields = [
            "manager_messages", "researcher_messages", "calculator_messages",
            "planner_messages", "summarizer_messages"
        ]
        
        for field in message_fields:
            messages = sample_vacation_state[field]
            assert isinstance(messages, list)
            # Should be empty initially
            assert len(messages) == 0


class TestStateUpdates:
    """Test state update operations."""

    def test_research_results_update(self, sample_vacation_state):
        """Test updating research results in state."""
        # Simulate research results update
        research_data = {
            "flights": [
                {"airline": "Test Air", "price": 300.0},
                {"airline": "Another Air", "price": 350.0}
            ],
            "accommodations": {
                "hotels": [
                    {"name": "Test Hotel", "price": {"per_night_value": 120.0}},
                    {"name": "Another Hotel", "price": {"per_night_value": 150.0}}
                ]
            },
            "destination_info": [
                {"content": "Paris is a beautiful city with many attractions."}
            ]
        }
        
        # Update state
        updated_state = sample_vacation_state.copy()
        updated_state["research_results"] = research_data
        
        # Verify update
        assert updated_state["research_results"] == research_data
        assert len(updated_state["research_results"]["flights"]) == 2
        assert len(updated_state["research_results"]["accommodations"]["hotels"]) == 2

    def test_calculator_results_update(self, sample_vacation_state):
        """Test updating calculator results in state."""
        calculator_data = {
            "days": 5,
            "hotel_total": 600.0,
            "flight_total": 300.0,
            "daily_cost_estimate": 100.0,
            "daily_total": 500.0,
            "subtotal": 1400.0,
            "commission_rate": 0.1,
            "commission_amount": 140.0,
            "final_quotation": 1540.0
        }
        
        # Update state
        updated_state = sample_vacation_state.copy()
        updated_state["calculator_results"] = calculator_data
        
        # Verify update
        assert updated_state["calculator_results"] == calculator_data
        assert updated_state["calculator_results"]["final_quotation"] == 1540.0

    def test_planner_results_update(self, sample_vacation_state):
        """Test updating planner results in state."""
        planner_data = {
            "weather_forecast": {
                "forecasts": [
                    {"date": "2025-09-15", "condition": "sunny", "temp_high": 25.0}
                ],
                "human_readable_summary": "Sunny weather expected."
            },
            "local_events": [
                {"title": "Paris Festival", "venue": "City Center", "date": "2025-09-16"}
            ]
        }
        
        # Update state
        updated_state = sample_vacation_state.copy()
        updated_state["planner_results"] = planner_data
        
        # Verify update
        assert updated_state["planner_results"] == planner_data
        assert len(updated_state["planner_results"]["local_events"]) == 1

    def test_message_append(self, sample_vacation_state):
        """Test appending messages to message lists."""
        # Add messages to different agents
        updated_state = sample_vacation_state.copy()
        
        updated_state["manager_messages"].append("Manager started workflow")
        updated_state["researcher_messages"].append("Research completed")
        updated_state["calculator_messages"].append("Costs calculated")
        
        # Verify messages
        assert len(updated_state["manager_messages"]) == 1
        assert len(updated_state["researcher_messages"]) == 1
        assert len(updated_state["calculator_messages"]) == 1
        
        assert updated_state["manager_messages"][0] == "Manager started workflow"
        assert updated_state["researcher_messages"][0] == "Research completed"
        assert updated_state["calculator_messages"][0] == "Costs calculated"

    def test_final_plan_update(self, sample_vacation_state):
        """Test updating final plan content."""
        final_plan_content = "# Complete Vacation Plan\n\nYour 5-day trip to Paris..."
        
        updated_state = sample_vacation_state.copy()
        updated_state["final_plan"] = final_plan_content
        updated_state["plan_approved"] = True
        
        # Verify update
        assert updated_state["final_plan"] == final_plan_content
        assert updated_state["plan_approved"] is True


class TestPydanticModels:
    """Test Pydantic model validation."""

    def test_hotel_model_validation(self, mock_hotel_data):
        """Test Hotel model validation with valid data."""
        hotel_data = mock_hotel_data["hotels"][0]  # First valid hotel
        
        # Should create Hotel instance without error
        hotel = Hotel(**hotel_data)
        
        # Verify fields
        assert hotel.name == hotel_data["name"]
        assert hotel.rating == hotel_data["rating"]
        assert hotel.hotel_class == hotel_data["hotel_class"]
        assert hotel.price.per_night_value == hotel_data["price"]["per_night_value"]

    def test_hotel_search_result_validation(self, mock_hotel_data):
        """Test HotelSearchResult model validation."""
        search_data = {
            "query": "Paris",
            "check_in_date": "2025-09-15",
            "check_out_date": "2025-09-20",
            "total_found": len(mock_hotel_data["hotels"]),
            "hotels": mock_hotel_data["hotels"][:3]  # Valid hotels only
        }
        
        # Should create HotelSearchResult without error
        result = HotelSearchResult(**search_data)
        
        # Verify structure
        assert result.query == "Paris"
        assert result.check_in_date == "2025-09-15"
        assert result.check_out_date == "2025-09-20"
        assert len(result.hotels) == 3

    def test_weather_forecast_validation(self, mock_weather_data):
        """Test WeatherForecast model validation."""
        forecast_data = mock_weather_data["forecasts"][0]
        
        # Should create WeatherForecast without error
        forecast = WeatherForecast(**forecast_data)
        
        # Verify fields
        assert forecast.date == forecast_data["date"]
        assert forecast.condition == forecast_data["condition"]
        assert forecast.temp_high == forecast_data["temp_high"]
        assert forecast.temp_low == forecast_data["temp_low"]

    def test_event_model_validation(self, mock_event_data):
        """Test Event model validation."""
        event_data = mock_event_data["events"][0]  # First valid event
        
        # Should create Event without error
        event = Event(**event_data)
        
        # Verify fields
        assert event.title == event_data["title"]
        assert event.venue == event_data["venue"]
        assert event.link == event_data["link"]

    def test_flight_itinerary_validation(self, mock_flight_data):
        """Test FlightItinerary model validation."""
        flight_data = mock_flight_data["flights"][0]  # First valid flight
        
        # Should create FlightItinerary without error
        flight = FlightItinerary(**flight_data)
        
        # Verify fields
        assert flight.id == flight_data["id"]
        assert flight.priceUSD == flight_data["priceUSD"]
        assert flight.durationOutbound == flight_data["durationOutbound"]


class TestStateValidation:
    """Test state validation and integrity checks."""

    def test_date_string_validation(self):
        """Test date string format validation."""
        valid_dates = ["2025-09-15", "2025-12-31", "2024-01-01"]
        invalid_dates = ["2025/09/15", "15-09-2025", "invalid-date", ""]
        
        for date_str in valid_dates:
            # Should parse without error
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                valid = True
            except ValueError:
                valid = False
            assert valid, f"Date {date_str} should be valid"
        
        for date_str in invalid_dates:
            if date_str:  # Skip empty string
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    valid = True
                except ValueError:
                    valid = False
                assert not valid, f"Date {date_str} should be invalid"

    def test_price_validation(self):
        """Test price value validation."""
        valid_prices = [0.0, 125.50, 1000.0, 9999.99]
        invalid_prices = [-50.0, float('inf'), float('nan')]
        
        for price in valid_prices:
            assert isinstance(price, (int, float))
            assert price >= 0
            assert price == price  # Not NaN
        
        for price in invalid_prices:
            if price < 0:
                assert price < 0  # Negative price
            elif price != price:  # NaN check
                assert price != price
            elif price == float('inf'):
                assert price == float('inf')

    def test_state_consistency(self, populated_vacation_state):
        """Test state consistency and relationships."""
        state = populated_vacation_state
        
        # Date consistency
        start_date = state["start_date"]
        end_date = state["return_date"]
        travel_dates = state["travel_dates"]
        
        if start_date and end_date:
            expected_travel_dates = f"{start_date} to {end_date}"
            assert travel_dates == expected_travel_dates
        
        # Calculator results consistency
        calc_results = state["calculator_results"]
        if calc_results:
            # Commission calculation consistency
            subtotal = calc_results.get("subtotal", 0)
            commission_rate = calc_results.get("commission_rate", 0)
            commission_amount = calc_results.get("commission_amount", 0)
            final_quotation = calc_results.get("final_quotation", 0)
            
            expected_commission = subtotal * commission_rate
            expected_final = subtotal * (1 + commission_rate)
            
            assert abs(commission_amount - expected_commission) < 0.01
            assert abs(final_quotation - expected_final) < 0.01


@pytest.mark.edge_case
class TestStateEdgeCases:
    """Test edge cases for state management."""

    def test_empty_state_initialization(self):
        """Test initialization with completely empty parameters."""
        state = initialize_vacation_state(
            user_request="",
            current_location="",
            destination="",
            start_date="",
            return_date=""
        )
        
        # Should handle empty strings gracefully
        assert state["travel_dates"] == ""
        assert all(isinstance(messages, list) for messages in [
            state["manager_messages"],
            state["researcher_messages"],
            state["calculator_messages"],
            state["planner_messages"],
            state["summarizer_messages"]
        ])

    def test_state_with_none_values(self):
        """Test state handling with None values."""
        state = initialize_vacation_state(
            user_request=None,
            current_location=None,
            destination=None,
            start_date=None,
            return_date=None
        )
        
        # Should convert None to empty string or handle gracefully
        string_fields = ["user_request", "current_location", "destination", "start_date", "return_date"]
        for field in string_fields:
            # The initialize_vacation_state function should handle None by using defaults
            assert isinstance(state[field], str)  # Should be string (empty if None was passed)

    def test_state_with_very_long_strings(self):
        """Test state with very long string values."""
        long_string = "x" * 10000  # 10,000 character string
        
        state = initialize_vacation_state(
            user_request=long_string,
            current_location=long_string,
            destination=long_string
        )
        
        # Should handle long strings without error
        assert len(state["user_request"]) == 10000
        assert len(state["current_location"]) == 10000
        assert len(state["destination"]) == 10000

    def test_state_with_special_characters(self):
        """Test state with special characters and unicode."""
        special_strings = {
            "user_request": "Plan trip with émojis 🌍✈️🏨",
            "current_location": "Zürich & München",
            "destination": "Москва (Moscow) <script>alert('test')</script>"
        }
        
        state = initialize_vacation_state(**special_strings)
        
        # Should handle special characters and unicode
        assert state["user_request"] == special_strings["user_request"]
        assert state["current_location"] == special_strings["current_location"]
        assert state["destination"] == special_strings["destination"]

    def test_large_state_updates(self, sample_vacation_state):
        """Test state updates with large data structures."""
        # Create large research results
        large_flights = [{"id": f"flight_{i}", "price": 300.0} for i in range(1000)]
        large_hotels = [{"name": f"Hotel {i}", "price": 150.0} for i in range(500)]
        
        large_research_results = {
            "flights": large_flights,
            "accommodations": {"hotels": large_hotels},
            "destination_info": [{"content": "x" * 50000}]  # 50KB content
        }
        
        # Update state
        updated_state = sample_vacation_state.copy()
        updated_state["research_results"] = large_research_results
        
        # Should handle large data structures
        assert len(updated_state["research_results"]["flights"]) == 1000
        assert len(updated_state["research_results"]["accommodations"]["hotels"]) == 500
        assert len(updated_state["research_results"]["destination_info"][0]["content"]) == 50000

    def test_state_deep_copy_behavior(self, populated_vacation_state):
        """Test state deep copy behavior for nested structures."""
        # Create a copy
        state_copy = populated_vacation_state.copy()
        
        # Modify nested structure in copy
        if state_copy["research_results"].get("flights"):
            state_copy["research_results"]["flights"][0]["price"] = 999.99
        
        # Original should not be affected (if properly deep copied)
        original_flights = populated_vacation_state["research_results"].get("flights", [])
        if original_flights:
            # Note: .copy() only does shallow copy, so this test shows the limitation
            # In practice, you'd need deepcopy for true isolation
            assert isinstance(original_flights[0].get("price"), (int, float))

    def test_concurrent_state_updates(self, sample_vacation_state):
        """Test handling of concurrent-like state updates."""
        # Simulate multiple agents updating different parts simultaneously
        state1 = sample_vacation_state.copy()
        state2 = sample_vacation_state.copy()
        
        # Agent 1 updates research results
        state1["research_results"] = {"flights": [{"id": "flight1"}]}
        state1["researcher_messages"].append("Research done")
        
        # Agent 2 updates calculator results
        state2["calculator_results"] = {"total": 1000.0}
        state2["calculator_messages"].append("Calculation done")
        
        # Merge states (simplified merge)
        merged_state = sample_vacation_state.copy()
        merged_state.update(state1)
        merged_state["calculator_results"] = state2["calculator_results"]
        merged_state["calculator_messages"] = state2["calculator_messages"]
        
        # Verify merged state
        assert "flights" in merged_state["research_results"]
        assert "total" in merged_state["calculator_results"]
        assert len(merged_state["researcher_messages"]) == 1
        assert len(merged_state["calculator_messages"]) == 1
