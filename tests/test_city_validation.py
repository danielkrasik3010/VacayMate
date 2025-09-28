"""
Unit tests for city validation functionality.

Tests cover:
- City validation logic
- Error message generation
- Integration with VacayMate system
- Edge cases and error handling
"""

import pytest
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from tools.city_mapping import is_valid_city, get_city_validation_error, get_city_code
from VacayMate_system import VacayMate


class TestCityValidation:
    """Test city validation functionality."""

    def test_valid_cities(self):
        """Test validation of valid cities."""
        valid_cities = [
            "Barcelona", "barcelona", "BARCELONA",
            "Paris", "paris", 
            "New York", "new york", "new-york",
            "Los Angeles", "los angeles",
            "Tokyo", "tokyo",
            "London", "london"
        ]
        
        for city in valid_cities:
            assert is_valid_city(city), f"{city} should be valid"

    def test_invalid_cities(self):
        """Test validation of invalid cities."""
        invalid_cities = [
            "InvalidCity", "NonExistentPlace", "XYZ123", 
            "Fake Town", "Unknown", "", "   ", None
        ]
        
        for city in invalid_cities:
            assert not is_valid_city(city), f"{city} should be invalid"

    def test_city_validation_case_insensitive(self):
        """Test that city validation is case insensitive."""
        test_cases = [
            ("barcelona", True),
            ("Barcelona", True),
            ("BARCELONA", True),
            ("BarCeLonA", True),
            ("paris", True),
            ("PARIS", True),
            ("invalidcity", False),
            ("INVALIDCITY", False)
        ]
        
        for city, expected in test_cases:
            result = is_valid_city(city)
            assert result == expected, f"{city} validation should return {expected}"

    def test_city_validation_with_spaces_and_hyphens(self):
        """Test city validation with spaces and hyphens."""
        test_cases = [
            ("New York", True),
            ("new york", True),
            ("new-york", True),
            ("newyork", True),
            ("Los Angeles", True),
            ("los angeles", True),
            ("los-angeles", True),
            ("losangeles", True)
        ]
        
        for city, expected in test_cases:
            result = is_valid_city(city)
            assert result == expected, f"{city} validation should return {expected}"

    def test_partial_city_matches(self):
        """Test partial city name matching."""
        # These should work due to partial matching
        partial_matches = [
            ("Barce", True),  # Matches Barcelona
            ("Lond", True),   # Matches London
            ("Tok", True),    # Matches Tokyo
        ]
        
        for city, expected in partial_matches:
            result = is_valid_city(city)
            assert result == expected, f"{city} partial match should return {expected}"


class TestCityValidationErrors:
    """Test city validation error messages."""

    def test_empty_city_error(self):
        """Test error message for empty city."""
        error = get_city_validation_error("", "Test Field")
        assert "Test Field is required" in error
        assert "Please enter a valid city name" in error

    def test_invalid_city_error_with_suggestions(self):
        """Test error message for invalid city with suggestions."""
        # Test with a city that should generate suggestions
        error = get_city_validation_error("Barcelon", "Departure City")
        
        assert "'Barcelon' is not a valid city" in error
        assert "Departure City" not in error  # Should use the city name
        assert "Supported cities include" in error

    def test_completely_invalid_city_error(self):
        """Test error message for completely invalid city."""
        error = get_city_validation_error("XYZ123", "Destination")
        
        assert "'XYZ123' is not a valid city" in error
        assert "Please check the spelling" in error
        assert "Supported cities include" in error

    def test_error_message_field_names(self):
        """Test error messages with different field names."""
        test_cases = [
            ("InvalidCity", "Departure City"),
            ("FakePlace", "Destination"),
            ("Unknown", "City")
        ]
        
        for city, field_name in test_cases:
            error = get_city_validation_error(city, field_name)
            assert isinstance(error, str)
            assert len(error) > 50  # Should be a substantial error message
            assert f"'{city}' is not a valid city" in error


class TestVacayMateValidation:
    """Test VacayMate system validation integration."""

    def test_vacaymate_validate_cities_valid(self):
        """Test VacayMate validate_cities method with valid cities."""
        vacay_mate = VacayMate()
        
        errors = vacay_mate.validate_cities("Barcelona", "Paris")
        assert errors == {}, "Valid cities should not produce errors"

    def test_vacaymate_validate_cities_invalid_departure(self):
        """Test VacayMate validate_cities method with invalid departure city."""
        vacay_mate = VacayMate()
        
        errors = vacay_mate.validate_cities("InvalidCity", "Paris")
        assert "departure_city" in errors
        assert "InvalidCity" in errors["departure_city"]
        assert "destination" not in errors

    def test_vacaymate_validate_cities_invalid_destination(self):
        """Test VacayMate validate_cities method with invalid destination."""
        vacay_mate = VacayMate()
        
        errors = vacay_mate.validate_cities("Barcelona", "InvalidPlace")
        assert "destination" in errors
        assert "InvalidPlace" in errors["destination"]
        assert "departure_city" not in errors

    def test_vacaymate_validate_cities_both_invalid(self):
        """Test VacayMate validate_cities method with both cities invalid."""
        vacay_mate = VacayMate()
        
        errors = vacay_mate.validate_cities("InvalidDeparture", "InvalidDestination")
        assert "departure_city" in errors
        assert "destination" in errors
        assert "InvalidDeparture" in errors["departure_city"]
        assert "InvalidDestination" in errors["destination"]

    def test_vacaymate_run_with_valid_cities(self):
        """Test VacayMate run method with valid cities (should not raise)."""
        vacay_mate = VacayMate()
        
        # This should not raise a ValueError due to city validation
        # (it might raise other errors due to missing API keys, but not validation errors)
        try:
            result = vacay_mate.run(
                user_request="Test trip",
                current_location="Barcelona", 
                destination="Paris",
                start_date="2025-09-15",
                return_date="2025-09-20"
            )
            # If we get here, validation passed (other errors are OK for this test)
            assert True
        except ValueError as e:
            # Check if it's a city validation error
            error_msg = str(e)
            if "Error:" in error_msg and ("Barcelona" in error_msg or "Paris" in error_msg):
                pytest.fail(f"City validation failed for valid cities: {error_msg}")
            # Other ValueErrors are OK (e.g., API key issues)
        except Exception:
            # Other exceptions are OK for this test
            pass

    def test_vacaymate_run_with_invalid_cities(self):
        """Test VacayMate run method with invalid cities (should raise ValueError)."""
        vacay_mate = VacayMate()
        
        with pytest.raises(ValueError) as exc_info:
            vacay_mate.run(
                user_request="Test trip",
                current_location="InvalidDeparture",
                destination="InvalidDestination", 
                start_date="2025-09-15",
                return_date="2025-09-20"
            )
        
        error_msg = str(exc_info.value)
        assert "Departure City Error:" in error_msg
        assert "Destination Error:" in error_msg
        assert "InvalidDeparture" in error_msg
        assert "InvalidDestination" in error_msg

    def test_vacaymate_run_with_mixed_validity(self):
        """Test VacayMate run method with one valid and one invalid city."""
        vacay_mate = VacayMate()
        
        # Test invalid departure, valid destination
        with pytest.raises(ValueError) as exc_info:
            vacay_mate.run(
                user_request="Test trip",
                current_location="InvalidCity",
                destination="Paris",
                start_date="2025-09-15", 
                return_date="2025-09-20"
            )
        
        error_msg = str(exc_info.value)
        assert "Departure City Error:" in error_msg
        assert "InvalidCity" in error_msg
        # Should not mention destination since it's valid
        assert "Destination Error:" not in error_msg


@pytest.mark.edge_case
class TestCityValidationEdgeCases:
    """Test edge cases for city validation."""

    def test_validation_with_none_input(self):
        """Test validation with None input."""
        assert not is_valid_city(None)
        
        error = get_city_validation_error(None, "Test Field")
        assert "Test Field is required" in error

    def test_validation_with_empty_strings(self):
        """Test validation with various empty string formats."""
        empty_inputs = ["", "   ", "\t", "\n", "  \t  \n  "]
        
        for empty_input in empty_inputs:
            assert not is_valid_city(empty_input)
            
            error = get_city_validation_error(empty_input, "City")
            assert "is required" in error

    def test_validation_with_non_string_input(self):
        """Test validation with non-string input."""
        non_string_inputs = [123, [], {}, True, False]
        
        for non_string_input in non_string_inputs:
            assert not is_valid_city(non_string_input)

    def test_validation_with_very_long_input(self):
        """Test validation with very long city names."""
        long_city = "A" * 1000  # 1000 character string
        
        assert not is_valid_city(long_city)
        
        error = get_city_validation_error(long_city, "City")
        assert isinstance(error, str)
        assert len(error) > 50

    def test_validation_with_special_characters(self):
        """Test validation with special characters."""
        special_cities = [
            "City@#$%",
            "City<script>",
            "City\x00null",
            "City\u200b",  # Zero-width space
        ]
        
        for city in special_cities:
            # These should all be invalid
            assert not is_valid_city(city)

    def test_city_code_generation_for_invalid_cities(self):
        """Test that city codes are still generated for invalid cities."""
        invalid_city = "InvalidTestCity"
        
        # Should still return a formatted code
        code = get_city_code(invalid_city)
        assert code == "City:invalidtestcity_xx"
        
        # But validation should fail
        assert not is_valid_city(invalid_city)
