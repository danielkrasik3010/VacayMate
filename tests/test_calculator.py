"""
Unit tests for VacayMate calculator functionality.

Tests cover:
- Cost calculations and aggregations
- Commission rate applications
- Price averaging and totaling
- Currency formatting and validation
- Mathematical accuracy and rounding
"""

import pytest
import statistics
from decimal import Decimal
from unittest.mock import Mock, patch
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from tools.Make_quotation_tool import make_quotation, ask_llm_for_daily_cost


class TestCostCalculations:
    """Test core cost calculation logic."""

    def test_hotel_cost_calculation(self, sample_prices, sample_dates):
        """Test hotel cost calculation accuracy."""
        hotel_prices = sample_prices["hotel_prices"]
        days = 5
        
        # Calculate expected total
        avg_price = statistics.mean(hotel_prices)
        expected_total = avg_price * days
        
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            result = make_quotation.invoke({
                "hotel_prices": hotel_prices,
                "flight_prices": [300.0],
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Paris"
            })
        
        assert abs(result["hotel_total"] - expected_total) < 0.01

    def test_flight_cost_calculation(self, sample_prices, sample_dates):
        """Test flight cost calculation (average of round-trip prices)."""
        flight_prices = sample_prices["flight_prices"]
        expected_avg = statistics.mean(flight_prices)
        
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            result = make_quotation.invoke({
                "hotel_prices": [100.0],
                "flight_prices": flight_prices,
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Barcelona"
            })
        
        assert abs(result["flight_total"] - expected_avg) < 0.01

    def test_daily_cost_calculation(self, sample_dates):
        """Test daily cost calculation and aggregation."""
        daily_cost = 125.0
        days = 5
        expected_total = daily_cost * days
        
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=daily_cost):
            result = make_quotation.invoke({
                "hotel_prices": [100.0],
                "flight_prices": [300.0],
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Madrid"
            })
        
        assert result["daily_cost_estimate"] == daily_cost
        assert result["daily_total"] == expected_total

    def test_subtotal_calculation(self, sample_dates):
        """Test subtotal calculation (hotel + flight + daily costs)."""
        hotel_price = 120.0
        flight_price = 300.0
        daily_cost = 100.0
        days = 5
        
        expected_hotel_total = hotel_price * days
        expected_daily_total = daily_cost * days
        expected_subtotal = expected_hotel_total + flight_price + expected_daily_total
        
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=daily_cost):
            result = make_quotation.invoke({
                "hotel_prices": [hotel_price],
                "flight_prices": [flight_price],
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Rome"
            })
        
        assert abs(result["subtotal"] - expected_subtotal) < 0.01

    def test_commission_calculation(self, sample_dates):
        """Test commission calculation accuracy."""
        subtotal = 1000.0
        commission_rate = 0.1
        expected_commission = subtotal * commission_rate
        expected_final = subtotal * (1 + commission_rate)
        
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=80.0):
            # Set up prices to achieve desired subtotal
            result = make_quotation.invoke({
                "hotel_prices": [100.0],  # 100 * 5 = 500
                "flight_prices": [100.0], # 100
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],  # 5 days
                "destination": "Amsterdam"
                # Daily costs: 80 * 5 = 400
                # Total: 500 + 100 + 400 = 1000
            })
        
        assert result["commission_rate"] == commission_rate
        assert abs(result["commission_amount"] - expected_commission) < 0.01
        assert abs(result["final_quotation"] - expected_final) < 0.01

    def test_complex_calculation_accuracy(self):
        """Test complex calculation with multiple price points."""
        hotel_prices = [125.50, 98.75, 156.25, 142.00, 133.50]
        flight_prices = [285.50, 312.00, 298.75]
        daily_cost = 115.25
        days = 7
        
        # Manual calculations
        avg_hotel = statistics.mean(hotel_prices)
        hotel_total = avg_hotel * days
        avg_flight = statistics.mean(flight_prices)
        daily_total = daily_cost * days
        subtotal = hotel_total + avg_flight + daily_total
        commission = subtotal * 0.1
        final_quotation = subtotal * 1.1
        
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=daily_cost):
            result = make_quotation.invoke({
                "hotel_prices": hotel_prices,
                "flight_prices": flight_prices,
                "start_date": "2025-09-15",
                "end_date": "2025-09-22",  # 7 days
                "destination": "Vienna"
            })
        
        # Verify all calculations
        assert abs(result["hotel_total"] - hotel_total) < 0.01
        assert abs(result["flight_total"] - avg_flight) < 0.01
        assert abs(result["daily_total"] - daily_total) < 0.01
        assert abs(result["subtotal"] - subtotal) < 0.01
        assert abs(result["commission_amount"] - commission) < 0.01
        assert abs(result["final_quotation"] - final_quotation) < 0.01


class TestPriceAveraging:
    """Test price averaging functionality."""

    def test_simple_average(self):
        """Test simple price averaging."""
        prices = [100.0, 200.0, 300.0]
        expected_avg = 200.0
        result = statistics.mean(prices)
        assert result == expected_avg

    def test_single_price_average(self):
        """Test averaging with single price."""
        prices = [150.0]
        expected_avg = 150.0
        result = statistics.mean(prices)
        assert result == expected_avg

    def test_decimal_precision_average(self):
        """Test averaging with high decimal precision."""
        prices = [99.999, 100.001, 100.000]
        expected_avg = 100.0
        result = statistics.mean(prices)
        assert abs(result - expected_avg) < 0.001

    def test_large_number_average(self):
        """Test averaging with large numbers."""
        prices = [5000.0, 10000.0, 15000.0]
        expected_avg = 10000.0
        result = statistics.mean(prices)
        assert result == expected_avg

    def test_mixed_precision_average(self):
        """Test averaging with mixed precision numbers."""
        prices = [125, 125.5, 125.25, 125.75]
        expected_avg = 125.375
        result = statistics.mean(prices)
        assert abs(result - expected_avg) < 0.001


class TestRoundingBehavior:
    """Test monetary value rounding behavior."""

    def test_standard_rounding(self):
        """Test standard rounding to 2 decimal places."""
        test_cases = [
            (123.456, 123.46),
            (123.454, 123.45),
            (123.455, 123.45),  # Python uses banker's rounding
            (0.999, 1.00),
            (0.001, 0.00)
        ]
        
        for input_val, expected in test_cases:
            result = round(input_val, 2)
            assert result == expected

    def test_commission_rounding(self):
        """Test commission calculation rounding."""
        test_cases = [
            (1000.0, 0.1, 100.00),
            (999.99, 0.1, 100.00),
            (1234.567, 0.1, 123.46),
            (0.01, 0.1, 0.00)
        ]
        
        for subtotal, rate, expected in test_cases:
            commission = round(subtotal * rate, 2)
            assert commission == expected

    def test_final_quotation_rounding(self):
        """Test final quotation rounding."""
        test_cases = [
            (1000.0, 1100.00),
            (999.99, 1099.99),
            (1234.567, 1358.02),  # 1234.567 * 1.1 = 1358.0237
        ]
        
        for subtotal, expected in test_cases:
            final_quotation = round(subtotal * 1.1, 2)
            assert final_quotation == expected


class TestCommissionRates:
    """Test commission rate applications."""

    def test_default_commission_rate(self, sample_dates):
        """Test default 10% commission rate."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            result = make_quotation.invoke({
                "hotel_prices": [100.0],
                "flight_prices": [200.0],
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Berlin"
            })
        
        assert result["commission_rate"] == 0.1

    def test_commission_amount_accuracy(self):
        """Test commission amount calculation accuracy."""
        test_cases = [
            (1000.0, 100.0),
            (500.0, 50.0),
            (1234.56, 123.46),
            (0.0, 0.0)
        ]
        
        for subtotal, expected_commission in test_cases:
            commission = round(subtotal * 0.1, 2)
            assert commission == expected_commission

    def test_final_price_with_commission(self):
        """Test final price calculation including commission."""
        test_cases = [
            (1000.0, 1100.0),
            (500.0, 550.0),
            (1234.56, 1358.02),
            (0.0, 0.0)
        ]
        
        for subtotal, expected_final in test_cases:
            final_price = round(subtotal * 1.1, 2)
            assert final_price == expected_final


class TestMathematicalAccuracy:
    """Test mathematical accuracy and precision."""

    def test_floating_point_precision(self):
        """Test floating point precision in calculations."""
        # Test case that might cause floating point errors
        prices = [0.1, 0.2, 0.3]
        result = sum(prices)
        expected = 0.6
        
        # Should be close due to floating point representation
        assert abs(result - expected) < 1e-10

    def test_large_number_calculations(self, sample_dates):
        """Test calculations with large numbers."""
        large_prices = [50000.0, 75000.0, 100000.0]
        
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=5000.0):
            result = make_quotation.invoke({
                "hotel_prices": large_prices,
                "flight_prices": [25000.0],
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Monaco"
            })
        
        # Should handle large numbers correctly
        assert result["final_quotation"] > 400000.0
        assert isinstance(result["final_quotation"], float)

    def test_decimal_accuracy_in_totals(self):
        """Test decimal accuracy in total calculations."""
        # Use Decimal for exact arithmetic verification
        hotel_price = Decimal('125.50')
        flight_price = Decimal('285.75')
        daily_cost = Decimal('95.25')
        days = 5
        
        expected_hotel_total = hotel_price * days
        expected_daily_total = daily_cost * days
        expected_subtotal = expected_hotel_total + flight_price + expected_daily_total
        expected_commission = expected_subtotal * Decimal('0.1')
        expected_final = expected_subtotal * Decimal('1.1')
        
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=float(daily_cost)):
            result = make_quotation.invoke({
                "hotel_prices": [float(hotel_price)],
                "flight_prices": [float(flight_price)],
                "start_date": "2025-09-15",
                "end_date": "2025-09-20",
                "destination": "Zurich"
            })
        
        # Compare with small tolerance for floating point
        assert abs(result["hotel_total"] - float(expected_hotel_total)) < 0.01
        assert abs(result["subtotal"] - float(expected_subtotal)) < 0.01
        assert abs(result["commission_amount"] - float(expected_commission)) < 0.01
        assert abs(result["final_quotation"] - float(expected_final)) < 0.01


class TestCurrencyHandling:
    """Test currency handling and formatting."""

    def test_price_string_parsing(self, sample_dates):
        """Test parsing of price strings with currency symbols."""
        # Note: Current make_quotation tool expects numeric values, not strings
        # This test documents that string parsing is not currently supported
        price_strings = ["$125.50", "$98.75", "$156.00"]
        
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            with pytest.raises(ValueError):  # Pydantic validation should fail
                make_quotation.invoke({
                    "hotel_prices": price_strings,
                    "flight_prices": ["$300.00"],
                    "start_date": sample_dates["start_date"],
                    "end_date": sample_dates["end_date"],
                    "destination": "New York"
                })

    def test_comma_separated_prices(self, sample_dates):
        """Test parsing of comma-separated price values."""
        # Note: Current make_quotation tool expects numeric values, not strings
        # This test documents that string parsing is not currently supported
        price_strings = ["$1,250.50", "$2,098.75", "$1,156.00"]
        
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=200.0):
            with pytest.raises(ValueError):  # Pydantic validation should fail
                make_quotation.invoke({
                    "hotel_prices": price_strings,
                    "flight_prices": ["$1,500.00"],
                    "start_date": sample_dates["start_date"],
                    "end_date": sample_dates["end_date"],
                    "destination": "Tokyo"
                })


@pytest.mark.edge_case
class TestCalculatorEdgeCases:
    """Test edge cases for calculator functionality."""

    def test_zero_prices(self, sample_dates):
        """Test calculation with zero prices."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=50.0):
            result = make_quotation.invoke({
                "hotel_prices": [0.0, 0.0],
                "flight_prices": [0.0],
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "TestCity"
            })
        
        assert result["hotel_total"] == 0.0
        assert result["flight_total"] == 0.0
        assert result["daily_total"] == 250.0  # 50 * 5 days
        assert result["subtotal"] == 250.0
        assert result["final_quotation"] == 275.0  # 250 * 1.1

    def test_single_day_trip(self):
        """Test calculation for single day trip."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=100.0):
            result = make_quotation.invoke({
                "hotel_prices": [150.0],
                "flight_prices": [300.0],
                "start_date": "2025-09-15",
                "end_date": "2025-09-16",  # 1 day
                "destination": "London"
            })
        
        assert result["days"] == 1
        assert result["hotel_total"] == 150.0
        assert result["daily_total"] == 100.0

    def test_same_day_trip(self):
        """Test calculation for same day trip (0 days)."""
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

    def test_very_long_trip(self):
        """Test calculation for very long trip."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=80.0):
            result = make_quotation.invoke({
                "hotel_prices": [100.0],
                "flight_prices": [500.0],
                "start_date": "2025-09-15",
                "end_date": "2025-10-15",  # 30 days
                "destination": "Australia"
            })
        
        assert result["days"] == 30
        assert result["hotel_total"] == 3000.0  # 100 * 30
        assert result["daily_total"] == 2400.0  # 80 * 30

    def test_extreme_price_values(self, sample_dates):
        """Test with extreme price values."""
        with patch('tools.Make_quotation_tool.ask_llm_for_daily_cost', return_value=10000.0):
            result = make_quotation.invoke({
                "hotel_prices": [50000.0],
                "flight_prices": [100000.0],
                "start_date": sample_dates["start_date"],
                "end_date": sample_dates["end_date"],
                "destination": "Private Island"
            })
        
        # Should handle extreme values
        assert result["hotel_total"] == 250000.0  # 50000 * 5
        assert result["flight_total"] == 100000.0
        assert result["daily_total"] == 50000.0  # 10000 * 5
        assert result["final_quotation"] == 440000.0  # 400000 * 1.1
