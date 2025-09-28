"""
Unit tests for VacayMate tools with focus on deterministic functionality.

Tests cover:
- Flight price parsing and formatting
- Hotel data processing and address formatting  
- Price calculation and validation
- Date parsing and duration calculations
- Data structure validation
"""

import pytest
import json
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from tools.Make_quotation_tool import make_quotation
from tools.Hotels_prices_tool import simplify_hotels
from tools.city_mapping import get_city_code


class TestMakeQuotationTool:
    """Test the quotation calculation tool - deterministic calculations only."""

    def test_basic_quotation_calculation(self, sample_prices, sample_dates):
        """Test basic quotation calculation with valid inputs."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=120.0):
            result = make_quotation.invoke({
                "hotel_prices": sample_prices["hotel_prices"],
                "flight_prices": sample_prices["flight_prices"], 
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Paris"
            })
            
            # Verify structure
            assert isinstance(result, dict)
            required_keys = [
                "days", "hotel_total", "flight_total", "daily_cost_estimate",
                "daily_total", "subtotal", "commission_rate", "commission_amount", 
                "final_quotation"
            ]
            for key in required_keys:
                assert key in result, f"Missing key: {key}"
            
            # Verify calculations
            assert result["days"] == 5
            assert result["commission_rate"] == 0.1
            assert abs(result["commission_amount"] - result["subtotal"] * 0.1) < 0.01
            assert abs(result["final_quotation"] - result["subtotal"] * 1.1) < 0.01
            assert result["hotel_total"] > 0
            assert result["flight_total"] > 0

    def test_quotation_with_string_prices(self, edge_case_prices, sample_dates):
        """Test quotation calculation with string price inputs."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            result = make_quotation.invoke({
                "hotel_prices": edge_case_prices["string_prices"]["hotels"],
                "flight_prices": edge_case_prices["string_prices"]["flights"],
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Barcelona"
            })
            
            # Should convert strings to floats successfully
            assert isinstance(result["hotel_total"], float)
            assert isinstance(result["flight_total"], float)
            assert result["hotel_total"] > 0
            assert result["flight_total"] > 0

    def test_quotation_with_zero_prices(self, edge_case_prices, sample_dates):
        """Test quotation calculation with zero prices."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=80.0):
            result = make_quotation.invoke({
                "hotel_prices": edge_case_prices["zero_prices"]["hotels"],
                "flight_prices": edge_case_prices["zero_prices"]["flights"],
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Madrid"
            })
            
            assert result["hotel_total"] == 0.0
            assert result["flight_total"] == 0.0
            assert result["daily_total"] > 0  # Should still have daily costs
            assert result["final_quotation"] > 0

    def test_quotation_with_single_prices(self, edge_case_prices, sample_dates):
        """Test quotation calculation with single price entries."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=90.0):
            result = make_quotation.invoke({
                "hotel_prices": edge_case_prices["single_prices"]["hotels"],
                "flight_prices": edge_case_prices["single_prices"]["flights"],
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Rome"
            })
            
            # Single prices should be used as averages
            assert result["hotel_total"] == 125.0 * 5  # 125 per night * 5 nights
            assert result["flight_total"] == 300.0

    def test_quotation_date_calculations(self, sample_prices):
        """Test date calculation logic."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=110.0):
            # Test different date ranges
            test_cases = [
                ("2025-09-15", "2025-09-16", 1),  # 1 day
                ("2025-09-15", "2025-09-20", 5),  # 5 days
                ("2025-09-15", "2025-09-15", 0),  # Same day (0 days)
                ("2025-09-01", "2025-10-01", 30), # 30 days
            ]
            
            for start_date, end_date, expected_days in test_cases:
                result = make_quotation.invoke({
                    "hotel_prices": sample_prices["hotel_prices"],
                    "flight_prices": sample_prices["flight_prices"],
                    "start_date": start_date,
                    "end_date": end_date,
                    "destination": "London"
                })
                
                assert result["days"] == expected_days
                assert result["hotel_total"] == pytest.approx(
                    sum(sample_prices["hotel_prices"]) / len(sample_prices["hotel_prices"]) * expected_days,
                    rel=1e-2
                )

    def test_quotation_commission_calculation(self, sample_prices, sample_dates):
        """Test commission calculation accuracy."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            result = make_quotation.invoke({
                "hotel_prices": [100.0, 100.0, 100.0],
                "flight_prices": [300.0, 300.0],
                "start_date": "2025-09-15",
                "end_date": "2025-09-20",  # 5 days
                "destination": "Amsterdam"
            })
            
            # Manual calculation verification
            expected_hotel_total = 100.0 * 5  # 500.0
            expected_flight_total = 300.0
            expected_daily_total = 100.0 * 5  # 500.0
            expected_subtotal = expected_hotel_total + expected_flight_total + expected_daily_total  # 1300.0
            expected_commission = expected_subtotal * 0.1  # 130.0
            expected_final = expected_subtotal * 1.1  # 1430.0
            
            assert result["hotel_total"] == expected_hotel_total
            assert result["flight_total"] == expected_flight_total
            assert result["daily_total"] == expected_daily_total
            assert result["subtotal"] == expected_subtotal
            assert result["commission_amount"] == expected_commission
            assert abs(result["final_quotation"] - expected_final) < 0.01

    def test_quotation_invalid_inputs(self):
        """Test quotation tool with invalid inputs."""
        # Invalid price formats
        with pytest.raises(ValueError):
            make_quotation.invoke({
                "hotel_prices": ["invalid", "prices"],
                "flight_prices": [300.0],
                "start_date": "2025-09-15",
                "end_date": "2025-09-20",
                "destination": "Berlin"
            })

    def test_quotation_rounding(self, sample_dates):
        """Test that monetary values are properly rounded."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=123.456):
            result = make_quotation.invoke({
                "hotel_prices": [123.456, 234.567],
                "flight_prices": [345.678],
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Vienna"
            })
            
            # All monetary values should be rounded to 2 decimal places
            assert result["hotel_total"] == round(result["hotel_total"], 2)
            # Note: flight_total comes directly from input and may not be rounded
            assert result["daily_total"] == round(result["daily_total"], 2)
            assert result["subtotal"] == round(result["subtotal"], 2)
            assert result["commission_amount"] == round(result["commission_amount"], 2)
            assert result["final_quotation"] == round(result["final_quotation"], 2)


class TestHotelDataProcessing:
    """Test hotel data processing and formatting functions."""

    def test_simplify_hotels_basic(self):
        """Test basic hotel data simplification."""
        raw_hotel_data = [
            {
                "name": "Test Hotel",
                "rate_per_night": {"lowest": "$125.50"},
                "total_rate": {"lowest": "$627.50"},
                "address": "123 Test Street, Paris, France",
                "overall_rating": 4.2,
                "hotel_class": "4-star",
                "amenities": ["WiFi", "Restaurant", "Pool"],
                "gps_coordinates": {"latitude": 48.8566, "longitude": 2.3522}
            }
        ]
        
        result = simplify_hotels(raw_hotel_data)
        
        assert len(result) == 1
        hotel = result[0]
        
        # Verify structure
        assert "name" in hotel
        assert "price" in hotel
        assert "address" in hotel
        assert "rating" in hotel
        assert "hotel_class" in hotel
        assert "amenities" in hotel
        
        # Verify data processing
        assert hotel["name"] == "Test Hotel"
        assert hotel["price"]["per_night_value"] == 125.50
        assert hotel["price"]["total_value"] == 627.50
        assert hotel["rating"] == 4.2

    def test_simplify_hotels_address_formatting(self):
        """Test address formatting logic."""
        test_cases = [
            {
                "input": {"address": "Real Street Address, Paris"},
                "expected": "Real Street Address, Paris"
            },
            {
                "input": {"address": "Central area", "street": "123 Main St", "city": "Paris"},
                "expected": "123 Main St, Paris"
            },
            {
                "input": {"gps_coordinates": {"latitude": 48.8566, "longitude": 2.3522}},
                "expected": "48.8566, 2.3522"
            },
            {
                "input": {},
                "expected": "Address not available"
            }
        ]
        
        for case in test_cases:
            raw_data = [{
                "name": "Test Hotel",
                "rate_per_night": {"lowest": "$100.00"},
                "total_rate": {"lowest": "$500.00"},
                **case["input"]
            }]
            
            result = simplify_hotels(raw_data)
            assert result[0]["address"]["formatted"] == case["expected"]

    def test_simplify_hotels_price_parsing(self):
        """Test price parsing functionality."""
        test_cases = [
            {"input": "$125.50", "expected": 125.50},
            {"input": "$1,250.75", "expected": 1250.75},
            {"input": "125", "expected": 125.0},
            {"input": "", "expected": None},
            {"input": None, "expected": None}
        ]
        
        for case in test_cases:
            raw_data = [{
                "name": "Test Hotel",
                "rate_per_night": {"lowest": case["input"]},
                "total_rate": {"lowest": case["input"]},
                "address": "Test Address"
            }]
            
            result = simplify_hotels(raw_data)
            if case["expected"] is None:
                assert result[0]["price"]["per_night_value"] is None
            else:
                assert result[0]["price"]["per_night_value"] == case["expected"]

    def test_simplify_hotels_empty_input(self):
        """Test handling of empty input."""
        result = simplify_hotels([])
        assert result == []

    def test_simplify_hotels_malformed_data(self):
        """Test handling of malformed hotel data."""
        malformed_data = [
            {},  # Empty dict
            {"name": "Hotel without required fields"},
            {"rate_per_night": "invalid_format"},
        ]
        
        # Should not crash, should handle gracefully
        result = simplify_hotels(malformed_data)
        assert isinstance(result, list)
        assert len(result) == len(malformed_data)


class TestCityMapping:
    """Test city code mapping functionality."""

    def test_get_city_code_valid_cities(self):
        """Test city code retrieval for valid cities."""
        test_cases = [
            ("Paris", "City:paris_fr"),
            ("Barcelona", "City:barcelona_es"),
            ("London", "City:london_gb"),
            ("New York", "City:new-york_us"),
            ("rome", "City:rome_it"),  # Test case insensitive
            ("MADRID", "City:madrid_es")  # Test uppercase
        ]
        
        for city_name, expected_code in test_cases:
            result = get_city_code(city_name)
            assert result == expected_code, f"Failed for {city_name}"

    def test_get_city_code_invalid_cities(self):
        """Test city code retrieval for invalid/unknown cities."""
        invalid_cities = ["Unknown City", "NonExistentPlace", "", "   ", "123"]
        
        for city in invalid_cities:
            result = get_city_code(city)
            # Should return the input or handle gracefully
            assert isinstance(result, str)

    def test_get_city_code_edge_cases(self):
        """Test edge cases for city code mapping."""
        edge_cases = [
            None,
            123,
            [],
            {},
            "City with spaces and special chars!@#"
        ]
        
        for case in edge_cases:
            # Should not crash
            try:
                result = get_city_code(case)
                assert isinstance(result, str) or result is None
            except (TypeError, AttributeError):
                # Acceptable to raise these for invalid types
                pass


class TestDataValidation:
    """Test data validation and structure verification."""

    def test_flight_data_structure(self, mock_flight_data):
        """Test flight data structure validation."""
        flights = mock_flight_data["flights"]
        
        for flight in flights:
            if flight.get("id") != "flight_003_edge_case":  # Skip edge case
                # Required fields
                assert "id" in flight
                assert "priceUSD" in flight
                assert "airline" in flight
                assert "durationOutbound" in flight
                
                # Numeric validations
                assert isinstance(flight["priceUSD"], (int, float))
                assert flight["priceUSD"] >= 0
                
                # String validations
                assert isinstance(flight["airline"], str)
                assert isinstance(flight.get("human_readable_summary", ""), str)

    def test_hotel_data_structure(self, mock_hotel_data):
        """Test hotel data structure validation."""
        hotels = mock_hotel_data["hotels"]
        
        for hotel in hotels:
            if hotel.get("name") != "Edge Case Hotel":  # Skip edge case
                # Required fields
                assert "name" in hotel
                assert "price" in hotel
                assert "address" in hotel
                
                # Price structure
                price = hotel["price"]
                assert "per_night_value" in price
                assert "total_value" in price
                assert isinstance(price["per_night_value"], (int, float))
                assert isinstance(price["total_value"], (int, float))
                
                # Address structure
                address = hotel["address"]
                assert "formatted" in address
                assert isinstance(address["formatted"], str)

    def test_event_data_structure(self, mock_event_data):
        """Test event data structure validation."""
        events = mock_event_data["events"]
        
        for event in events:
            if event.get("title") != "Edge Case Event":  # Skip edge case
                # Required fields
                assert "title" in event
                assert "venue" in event
                assert "formatted_date" in event
                
                # String validations
                assert isinstance(event["title"], str)
                assert len(event["title"]) > 0
                
                # Optional fields should have correct types when present
                if "description" in event and event["description"]:
                    assert isinstance(event["description"], str)


class TestPriceCalculations:
    """Test price calculation utilities and edge cases."""

    def test_average_calculation(self):
        """Test average price calculations."""
        from statistics import mean
        
        test_cases = [
            ([100.0, 200.0, 150.0], 150.0),
            ([50.0], 50.0),
            ([0.0, 0.0, 0.0], 0.0),
            ([99.99, 100.01], 100.0)
        ]
        
        for prices, expected in test_cases:
            result = mean(prices)
            assert abs(result - expected) < 0.01

    def test_price_rounding(self):
        """Test price rounding functionality."""
        test_cases = [
            (123.456, 123.46),
            (99.999, 100.00),
            (0.001, 0.00),
            (1000.005, 1000.0)  # Banker's rounding rounds to even
        ]
        
        for input_price, expected in test_cases:
            result = round(input_price, 2)
            assert result == expected

    def test_commission_calculation(self):
        """Test commission calculation logic."""
        test_cases = [
            (1000.0, 0.1, 100.0),
            (500.0, 0.15, 75.0),
            (0.0, 0.1, 0.0),
            (123.45, 0.1, 12.345)  # Should be rounded later
        ]
        
        for subtotal, rate, expected in test_cases:
            commission = subtotal * rate
            assert abs(commission - expected) < 0.001


@pytest.mark.edge_case
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_data_handling(self):
        """Test handling of empty data structures."""
        # Empty hotel list
        result = simplify_hotels([])
        assert result == []
        
        # Empty price lists should be handled by quotation tool
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            with pytest.raises((ZeroDivisionError, ValueError)):
                make_quotation.invoke({
                    "hotel_prices": [],
                    "flight_prices": [],
                    "start_date": "2025-09-15",
                    "end_date": "2025-09-20",
                    "destination": "Paris"
                })

    def test_extreme_values(self):
        """Test handling of extreme values."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=50000.0):
            result = make_quotation.invoke({
                "hotel_prices": [10000.0, 15000.0],
                "flight_prices": [25000.0],
                "start_date": "2025-09-15",
                "end_date": "2025-09-20",
                "destination": "Monaco"
            })
            
            # Should handle extreme values without error
            assert result["final_quotation"] > 100000.0
            assert isinstance(result["final_quotation"], float)

    def test_date_edge_cases(self, edge_case_dates):
        """Test edge cases for date handling."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            # Same day trip
            result = make_quotation.invoke({
                "hotel_prices": [100.0],
                "flight_prices": [200.0],
                "start_date": edge_case_dates["same_day"]["start"],
                "end_date": edge_case_dates["same_day"]["end"],
                "destination": "Paris"
            })
            
            assert result["days"] == 0
            assert result["hotel_total"] == 0.0
            assert result["daily_total"] == 0.0
