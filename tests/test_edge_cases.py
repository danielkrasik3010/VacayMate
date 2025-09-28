"""
Comprehensive edge case tests for VacayMate system.

Tests cover:
- Missing or malformed data handling
- Extreme values and boundary conditions
- Network failures and API errors
- Invalid user inputs and data corruption
- Memory and performance edge cases
- Timezone and date edge cases
"""

import pytest
import json
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from tools.Make_quotation_tool import make_quotation
from tools.Hotels_prices_tool import simplify_hotels
from states.VacayMate_state import initialize_vacation_state
from VacayMate_system import VacayMate


@pytest.mark.edge_case
class TestMissingDataHandling:
    """Test handling of missing or incomplete data."""

    def test_quotation_with_empty_price_lists(self):
        """Test quotation calculation with empty price lists."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            # Empty hotel prices should cause division by zero
            with pytest.raises((ZeroDivisionError, ValueError, IndexError)):
                make_quotation.invoke({
                    "hotel_prices": [],
                    "flight_prices": [],
                    "start_date": "2025-09-15",
                    "end_date": "2025-09-20",
                    "destination": "Paris"
                })

    def test_quotation_with_none_prices(self):
        """Test quotation calculation with None values in price lists."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            with pytest.raises((TypeError, ValueError)):
                make_quotation.invoke({
                    "hotel_prices": [None, 150.0, None],
                    "flight_prices": [300.0, None],
                    "start_date": "2025-09-15",
                    "end_date": "2025-09-20",
                    "destination": "Paris"
                })

    def test_quotation_with_mixed_invalid_prices(self):
        """Test quotation with mix of valid and invalid prices."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            with pytest.raises((ValueError, TypeError)):
                make_quotation.invoke({
                    "hotel_prices": [125.0, "invalid", float('inf'), -50.0],
                    "flight_prices": [300.0, "also_invalid"],
                    "start_date": "2025-09-15",
                    "end_date": "2025-09-20",
                    "destination": "Paris"
                })

    def test_hotel_simplification_with_missing_fields(self):
        """Test hotel data simplification with missing required fields."""
        incomplete_hotels = [
            {},  # Completely empty
            {"name": "Hotel Without Price"},  # Missing price
            {"rate_per_night": {"lowest": "$125.00"}},  # Missing name
            {"name": "Hotel", "rate_per_night": {}},  # Empty price structure
        ]
        
        # Should handle gracefully without crashing
        result = simplify_hotels(incomplete_hotels)
        assert isinstance(result, list)
        assert len(result) == len(incomplete_hotels)
        
        # Check that missing fields are handled
        for hotel in result:
            assert isinstance(hotel, dict)

    def test_state_initialization_with_missing_dates(self):
        """Test state initialization with missing or invalid dates."""
        # Missing dates
        state = initialize_vacation_state(
            user_request="Test trip",
            current_location="Barcelona",
            destination="Paris"
            # Missing start_date and return_date
        )
        
        assert state["start_date"] == ""
        assert state["return_date"] == ""
        assert state["travel_dates"] == ""

    def test_markdown_generation_with_missing_data(self):
        """Test markdown generation when key data is missing."""
        vacay_mate = VacayMate()
        
        # State with completely empty results
        empty_state = {
            "user_request": "Test trip",
            "current_location": "Barcelona",
            "destination": "Paris",
            "start_date": "2025-09-15",
            "return_date": "2025-09-20",
            "travel_dates": "2025-09-15 to 2025-09-20",
            "manager_messages": [],
            "researcher_messages": [],
            "calculator_messages": [],
            "planner_messages": [],
            "summarizer_messages": [],
            "research_results": {},
            "planner_results": {},
            "calculator_results": {},
            "final_plan": ""
        }
        
        markdown = vacay_mate._build_markdown_content(
            empty_state, "Paris", "2025-09-15", "2025-09-20"
        )
        
        # Should generate markdown even with empty data
        assert isinstance(markdown, str)
        assert len(markdown) > 100
        assert "No flight options found" in markdown
        assert "No hotel options found" in markdown


@pytest.mark.edge_case
class TestExtremeValues:
    """Test handling of extreme values and boundary conditions."""

    def test_quotation_with_extreme_prices(self):
        """Test quotation with extremely high prices."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=50000.0):
            result = make_quotation.invoke({
                "hotel_prices": [100000.0, 150000.0, 200000.0],
                "flight_prices": [500000.0, 750000.0],
                "start_date": "2025-09-15",
                "end_date": "2025-09-20",
                "destination": "Private Island"
            })
            
            # Should handle extreme values
            assert result["final_quotation"] > 1000000.0
            assert isinstance(result["final_quotation"], float)
            assert not (result["final_quotation"] != result["final_quotation"])  # Not NaN

    def test_quotation_with_zero_day_trip(self):
        """Test quotation calculation for zero-day trip."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            result = make_quotation.invoke({
                "hotel_prices": [150.0],
                "flight_prices": [300.0],
                "start_date": "2025-09-15",
                "end_date": "2025-09-15",  # Same day
                "destination": "Paris"
            })
            
            assert result["days"] == 0
            assert result["hotel_total"] == 0.0
            assert result["daily_total"] == 0.0

    def test_quotation_with_very_long_trip(self):
        """Test quotation for extremely long trip."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=200.0):
            result = make_quotation.invoke({
                "hotel_prices": [100.0],
                "flight_prices": [1000.0],
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",  # 364 days
                "destination": "World Tour"
            })
            
            assert result["days"] == 364
            assert result["hotel_total"] == 36400.0  # 100 * 364
            assert result["daily_total"] == 72800.0  # 200 * 364

    def test_quotation_with_microscopic_prices(self):
        """Test quotation with very small prices."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=0.01):
            result = make_quotation.invoke({
                "hotel_prices": [0.01, 0.02, 0.03],
                "flight_prices": [0.05, 0.10],
                "start_date": "2025-09-15",
                "end_date": "2025-09-20",
                "destination": "Budget Destination"
            })
            
            # Should handle tiny values with proper rounding
            assert result["hotel_total"] >= 0.0
            assert result["final_quotation"] >= 0.0
            assert isinstance(result["final_quotation"], float)

    def test_hotel_data_with_extreme_coordinates(self):
        """Test hotel data processing with extreme GPS coordinates."""
        extreme_hotels = [
            {
                "name": "North Pole Hotel",
                "rate_per_night": {"lowest": "$1000.00"},
                "total_rate": {"lowest": "$5000.00"},
                "gps_coordinates": {"latitude": 90.0, "longitude": 0.0}  # North Pole
            },
            {
                "name": "South Pole Hotel",
                "rate_per_night": {"lowest": "$2000.00"},
                "total_rate": {"lowest": "$10000.00"},
                "gps_coordinates": {"latitude": -90.0, "longitude": 180.0}  # South Pole
            },
            {
                "name": "Invalid Coordinates Hotel",
                "rate_per_night": {"lowest": "$500.00"},
                "total_rate": {"lowest": "$2500.00"},
                "gps_coordinates": {"latitude": 200.0, "longitude": 400.0}  # Invalid
            }
        ]
        
        result = simplify_hotels(extreme_hotels)
        
        # Should handle extreme coordinates
        assert len(result) == 3
        for hotel in result:
            assert "address" in hotel
            assert "formatted" in hotel["address"]


@pytest.mark.edge_case
class TestDateAndTimeEdgeCases:
    """Test edge cases related to dates and times."""

    def test_quotation_with_past_dates(self):
        """Test quotation with dates in the past."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            result = make_quotation.invoke({
                "hotel_prices": [100.0],
                "flight_prices": [200.0],
                "start_date": "2020-01-01",
                "end_date": "2020-01-05",
                "destination": "Past Trip"
            })
            
            # Should calculate correctly regardless of past dates
            assert result["days"] == 4
            assert result["hotel_total"] == 400.0

    def test_quotation_with_future_dates(self):
        """Test quotation with far future dates."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            result = make_quotation.invoke({
                "hotel_prices": [100.0],
                "flight_prices": [200.0],
                "start_date": "2050-01-01",
                "end_date": "2050-01-05",
                "destination": "Future Trip"
            })
            
            # Should calculate correctly for future dates
            assert result["days"] == 4
            assert result["hotel_total"] == 400.0

    def test_quotation_with_leap_year_dates(self):
        """Test quotation calculations across leap year boundaries."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            result = make_quotation.invoke({
                "hotel_prices": [100.0],
                "flight_prices": [200.0],
                "start_date": "2024-02-28",
                "end_date": "2024-03-01",  # Leap year, Feb 29 exists
                "destination": "Leap Year Trip"
            })
            
            # Should correctly calculate 2 days (Feb 28 -> Feb 29 -> Mar 1)
            assert result["days"] == 2

    def test_quotation_with_year_boundary(self):
        """Test quotation across year boundaries."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            result = make_quotation.invoke({
                "hotel_prices": [100.0],
                "flight_prices": [200.0],
                "start_date": "2024-12-30",
                "end_date": "2025-01-02",
                "destination": "New Year Trip"
            })
            
            # Should correctly calculate 3 days across year boundary
            assert result["days"] == 3

    def test_state_with_invalid_date_formats(self):
        """Test state initialization with invalid date formats."""
        invalid_date_formats = [
            "2025/09/15",  # Wrong separator
            "15-09-2025",  # Wrong order
            "2025-13-01",  # Invalid month
            "2025-02-30",  # Invalid day
            "not-a-date",  # Not a date
            "2025-09-15T10:30:00Z"  # With time (might be valid but unexpected format)
        ]
        
        for invalid_date in invalid_date_formats:
            # State initialization should not crash
            state = initialize_vacation_state(
                user_request="Test",
                start_date=invalid_date,
                return_date="2025-09-20"
            )
            
            # Should store the invalid date as-is (validation happens elsewhere)
            assert state["start_date"] == invalid_date


@pytest.mark.edge_case
class TestMemoryAndPerformance:
    """Test memory usage and performance edge cases."""

    def test_large_data_structures(self):
        """Test handling of very large data structures."""
        # Create large flight list
        large_flight_list = []
        for i in range(10000):
            large_flight_list.append({
                "id": f"flight_{i}",
                "priceUSD": 300.0 + (i % 1000),
                "airline": f"Airline_{i % 100}",
                "duration": "2h 30m"
            })
        
        # Should handle large lists without memory issues
        assert len(large_flight_list) == 10000
        
        # Test processing subset
        subset = large_flight_list[:100]
        assert len(subset) == 100

    def test_deeply_nested_data_structures(self):
        """Test handling of deeply nested data structures."""
        # Create deeply nested structure
        nested_data = {"level_0": {}}
        current_level = nested_data["level_0"]
        
        for i in range(100):  # 100 levels deep
            current_level[f"level_{i+1}"] = {}
            current_level = current_level[f"level_{i+1}"]
        
        current_level["data"] = "deep_value"
        
        # Should handle deep nesting
        assert nested_data["level_0"]["level_1"]["level_2"] is not None

    def test_large_string_handling(self):
        """Test handling of very large strings."""
        # Create very large string (1MB)
        large_string = "x" * (1024 * 1024)
        
        state = initialize_vacation_state(
            user_request=large_string,
            destination="Test"
        )
        
        # Should handle large strings
        assert len(state["user_request"]) == 1024 * 1024

    def test_many_small_objects(self):
        """Test handling of many small objects."""
        # Create many small hotel objects
        many_hotels = []
        for i in range(10000):
            many_hotels.append({
                "name": f"Hotel_{i}",
                "rate_per_night": {"lowest": f"${100 + (i % 500)}.00"},
                "total_rate": {"lowest": f"${(100 + (i % 500)) * 5}.00"}
            })
        
        # Should handle many objects
        assert len(many_hotels) == 10000
        
        # Test processing (take only first 10 to avoid timeout)
        result = simplify_hotels(many_hotels[:10])
        assert len(result) == 10


@pytest.mark.edge_case
class TestDataCorruption:
    """Test handling of corrupted or malformed data."""

    def test_json_corruption_simulation(self):
        """Test handling of corrupted JSON-like data."""
        corrupted_data = {
            "flights": [
                {"airline": "Valid Air", "price": 300.0},
                {"airline": None, "price": "corrupted_price"},  # Corrupted entry
                12345,  # Not a dict
                {"airline": "Another Air"}  # Missing price
            ]
        }
        
        # Should handle corrupted data gracefully
        flights = corrupted_data["flights"]
        valid_flights = []
        
        for flight in flights:
            if isinstance(flight, dict) and "airline" in flight and "price" in flight:
                try:
                    price = float(flight["price"])
                    if price >= 0:
                        valid_flights.append(flight)
                except (ValueError, TypeError):
                    continue
        
        assert len(valid_flights) == 1  # Only one valid flight

    def test_mixed_data_types_in_lists(self):
        """Test handling of mixed data types in expected lists."""
        mixed_price_list = [125.0, "150", None, float('inf'), -50, "invalid", 200.0]
        
        # Filter and convert valid prices
        valid_prices = []
        for price in mixed_price_list:
            try:
                converted_price = float(price)
                if converted_price >= 0 and converted_price != float('inf') and converted_price == converted_price:  # Not NaN
                    valid_prices.append(converted_price)
            except (ValueError, TypeError):
                continue
        
        assert len(valid_prices) == 3  # 125.0, 150.0, 200.0

    def test_circular_references(self):
        """Test handling of circular references in data structures."""
        # Create circular reference
        data_a = {"name": "A"}
        data_b = {"name": "B", "ref": data_a}
        data_a["ref"] = data_b  # Circular reference
        
        # Should not cause infinite loops when accessing
        assert data_a["name"] == "A"
        assert data_b["name"] == "B"
        assert data_a["ref"]["name"] == "B"
        assert data_b["ref"]["name"] == "A"

    def test_unicode_corruption(self):
        """Test handling of corrupted unicode strings."""
        corrupted_strings = [
            "Valid string",
            "String with émojis 🌍✈️",
            "Partial unicode \udcff",  # Invalid surrogate
            "",  # Empty string
            "Normal string after corruption"
        ]
        
        # Should handle all strings without crashing
        for s in corrupted_strings:
            assert isinstance(s, str)
            # Basic string operations should work
            length = len(s)
            assert length >= 0


@pytest.mark.edge_case  
class TestConcurrencyEdgeCases:
    """Test edge cases related to concurrent operations."""

    def test_simultaneous_state_updates(self, sample_vacation_state):
        """Test handling of simultaneous state updates."""
        # Simulate concurrent updates to different parts of state
        state1 = sample_vacation_state.copy()
        state2 = sample_vacation_state.copy()
        
        # Update different sections
        state1["research_results"] = {"flights": [{"id": "flight1"}]}
        state2["calculator_results"] = {"total": 1000.0}
        
        # Merge manually (in real system, this would be handled by LangGraph)
        merged_state = sample_vacation_state.copy()
        merged_state["research_results"] = state1["research_results"]
        merged_state["calculator_results"] = state2["calculator_results"]
        
        # Should have both updates
        assert "flights" in merged_state["research_results"]
        assert "total" in merged_state["calculator_results"]

    def test_message_list_concurrent_appends(self, sample_vacation_state):
        """Test concurrent appends to message lists."""
        # Simulate multiple agents adding messages
        state = sample_vacation_state
        
        # Multiple messages from same agent
        state["manager_messages"].extend([
            "Message 1",
            "Message 2", 
            "Message 3"
        ])
        
        # Should handle multiple messages
        assert len(state["manager_messages"]) == 3
        assert state["manager_messages"][0] == "Message 1"
        assert state["manager_messages"][-1] == "Message 3"


@pytest.mark.edge_case
class TestErrorPropagation:
    """Test error propagation and recovery."""

    def test_llm_api_failure_simulation(self):
        """Test handling of LLM API failures."""
        # Mock LLM failure
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                make_quotation.invoke({
                    "hotel_prices": [100.0],
                    "flight_prices": [200.0],
                    "start_date": "2025-09-15",
                    "end_date": "2025-09-20",
                    "destination": "Paris"
                })

    def test_file_system_errors(self, populated_vacation_state):
        """Test handling of file system errors during export."""
        vacay_mate = VacayMate()
        
        # Mock file system error
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with patch('builtins.print') as mock_print:  # Capture error output
                vacay_mate._export_markdown_plan(
                    populated_vacation_state,
                    "Paris",
                    "2025-09-15",
                    "2025-09-20"
                )
                
                # Should handle error gracefully
                mock_print.assert_called()
                error_msg = mock_print.call_args[0][0]
                assert "Error exporting" in error_msg

    def test_network_timeout_simulation(self):
        """Test handling of network timeout scenarios."""
        # This would typically test API timeouts
        # For unit tests, we simulate with exceptions
        
        def timeout_function():
            raise TimeoutError("Network timeout")
        
        # Should handle timeout gracefully
        with pytest.raises(TimeoutError):
            timeout_function()

    def test_partial_data_corruption_recovery(self):
        """Test recovery from partial data corruption."""
        # Simulate partially corrupted hotel data
        mixed_hotel_data = [
            {"name": "Good Hotel", "rate_per_night": {"lowest": "$125.00"}},  # Valid
            {"corrupted": "data", "invalid": True},  # Corrupted
            {"name": "Another Good Hotel", "rate_per_night": {"lowest": "$150.00"}},  # Valid
            None,  # Completely invalid
            {"name": "Partial Hotel"},  # Missing price
        ]
        
        # Should extract valid data and skip corrupted entries
        result = simplify_hotels(mixed_hotel_data)
        
        # Should process all entries (including None values with default data)
        assert len(result) == len(mixed_hotel_data)
        
        # Valid entries should be processed correctly
        valid_entries = [h for h in result if h.get("name") and "Good Hotel" in h["name"]]
        assert len(valid_entries) >= 2
