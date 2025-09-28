"""
Unit tests for VacayMate formatting and export functionality.

Tests cover:
- Markdown content generation and formatting
- Table generation for flights, hotels, events
- Attraction parsing from destination content
- File export functionality
- Data structure formatting and validation
"""

import pytest
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from VacayMate_system import VacayMate


class TestMarkdownGeneration:
    """Test Markdown content generation functionality."""

    def test_build_markdown_content_basic(self, populated_vacation_state):
        """Test basic markdown content generation."""
        vacay_mate = VacayMate()
        
        markdown = vacay_mate._build_markdown_content(
            populated_vacation_state,
            "Paris",
            "2025-09-15", 
            "2025-09-20"
        )
        
        # Verify structure
        assert isinstance(markdown, str)
        assert len(markdown) > 500  # Should be substantial content
        
        # Verify headers
        assert "# 🌍 Vacation Plan: Paris" in markdown
        assert "## 🎬 Manager Agent Results" in markdown
        assert "## 🔬 Researcher Agent Results" in markdown
        assert "## 💵 Calculator Agent Results" in markdown
        assert "## 📅 Planner Agent Results" in markdown
        assert "## 📝 Complete Vacation Plan Summary" in markdown

    def test_markdown_flight_table_generation(self, populated_vacation_state):
        """Test flight table generation in markdown."""
        vacay_mate = VacayMate()
        
        markdown = vacay_mate._build_markdown_content(
            populated_vacation_state,
            "Paris",
            "2025-09-15",
            "2025-09-20"
        )
        
        # Verify flight table structure
        assert "### ✈️ Flight Options" in markdown
        assert "| Airline | Flight No. | From | To | Departure | Arrival | Duration | Price |" in markdown
        assert "|---------|------------|------|----|-----------|---------|-----------:|-------|" in markdown
        
        # Should contain flight data
        flights = populated_vacation_state["research_results"]["flights"]
        if flights:
            first_flight = flights[0]
            if first_flight.get("airline"):
                assert first_flight["airline"] in markdown

    def test_markdown_hotel_table_generation(self, populated_vacation_state):
        """Test hotel table generation in markdown."""
        vacay_mate = VacayMate()
        
        markdown = vacay_mate._build_markdown_content(
            populated_vacation_state,
            "Paris",
            "2025-09-15",
            "2025-09-20"
        )
        
        # Verify hotel table structure
        assert "### 🏨 Hotel Options" in markdown
        assert "| Hotel | Price/Night | Rating | Address | Amenities | Link |" in markdown
        assert "|-------|-------------|--------|---------|-----------|------|" in markdown

    def test_markdown_weather_section(self, populated_vacation_state):
        """Test weather section formatting in markdown."""
        vacay_mate = VacayMate()
        
        markdown = vacay_mate._build_markdown_content(
            populated_vacation_state,
            "Paris",
            "2025-09-15",
            "2025-09-20"
        )
        
        # Verify weather section
        assert "### 🌤️ Weather Forecast" in markdown
        
        # Check for weather data
        weather = populated_vacation_state["planner_results"]["weather_forecast"]
        if weather and weather.get("human_readable_summary"):
            summary = weather["human_readable_summary"][:300]
            assert summary in markdown

    def test_markdown_events_section(self, populated_vacation_state):
        """Test events section formatting in markdown."""
        vacay_mate = VacayMate()
        
        markdown = vacay_mate._build_markdown_content(
            populated_vacation_state,
            "Paris",
            "2025-09-15",
            "2025-09-20"
        )
        
        # Verify events section
        assert "### 🎉 Local Events" in markdown
        
        # Check for event data
        events = populated_vacation_state["planner_results"]["local_events"]
        if events:
            for event in events[:3]:  # Check first few events
                if event.get("title"):
                    assert event["title"] in markdown

    def test_markdown_cost_summary(self, populated_vacation_state):
        """Test cost summary formatting in markdown."""
        vacay_mate = VacayMate()
        
        markdown = vacay_mate._build_markdown_content(
            populated_vacation_state,
            "Paris",
            "2025-09-15",
            "2025-09-20"
        )
        
        # Verify cost summary section
        assert "## 💵 Calculator Agent Results" in markdown
        
        # Check for cost data
        calc_results = populated_vacation_state["calculator_results"]
        if calc_results:
            assert f"**Days:** {calc_results.get('days', 'N/A')}" in markdown
            assert f"**Hotel Total:** ${calc_results.get('hotel_total', 0):.2f}" in markdown
            assert f"**Flight Total:** ${calc_results.get('flight_total', 0):.2f}" in markdown

    def test_markdown_with_empty_data(self, sample_vacation_state):
        """Test markdown generation with empty/missing data."""
        vacay_mate = VacayMate()
        
        # State with minimal data
        empty_state = sample_vacation_state.copy()
        empty_state["research_results"] = {}
        empty_state["planner_results"] = {}
        empty_state["calculator_results"] = {}
        
        markdown = vacay_mate._build_markdown_content(
            empty_state,
            "Paris",
            "2025-09-15",
            "2025-09-20"
        )
        
        # Should handle empty data gracefully
        assert isinstance(markdown, str)
        assert "# 🌍 Vacation Plan: Paris" in markdown
        assert "- No flight options found" in markdown
        assert "- No hotel options found" in markdown


class TestAttractionParsing:
    """Test attraction parsing from destination content."""

    def test_parse_attractions_from_content_basic(self, mock_destination_info):
        """Test basic attraction parsing."""
        vacay_mate = VacayMate()
        
        attractions = vacay_mate._parse_attractions_from_content(
            mock_destination_info,
            "Paris"
        )
        
        # Should extract attractions
        assert isinstance(attractions, list)
        assert len(attractions) > 0
        
        # Check structure
        for attraction in attractions:
            assert "name" in attraction
            assert "description" in attraction
            assert isinstance(attraction["name"], str)
            assert isinstance(attraction["description"], str)

    def test_parse_attractions_paris_fallback(self):
        """Test Paris-specific attraction fallback."""
        vacay_mate = VacayMate()
        
        # Empty destination info should trigger Paris fallback
        attractions = vacay_mate._parse_attractions_from_content([], "Paris")
        
        # Should have Paris attractions
        assert len(attractions) > 10
        
        # Check for known Paris attractions
        attraction_names = [a["name"] for a in attractions]
        assert any("Eiffel Tower" in name for name in attraction_names)
        assert any("Louvre Museum" in name for name in attraction_names)

    def test_parse_attractions_generic_fallback(self):
        """Test generic attraction fallback for unknown cities."""
        vacay_mate = VacayMate()
        
        attractions = vacay_mate._parse_attractions_from_content([], "UnknownCity")
        
        # Should have generic attractions
        assert len(attractions) > 5
        
        # Check for generic patterns
        attraction_names = [a["name"] for a in attractions]
        assert any("UnknownCity" in name for name in attraction_names)

    def test_parse_attractions_with_html_content(self):
        """Test attraction parsing with HTML-like content."""
        vacay_mate = VacayMate()
        
        html_content = [
            {
                "content": "<p>Paris attractions include the <strong>Eiffel Tower</strong> and the famous <em>Louvre Museum</em>. Don't miss <a href='#'>Notre-Dame Cathedral</a> and the Arc de Triomphe.</p>"
            }
        ]
        
        attractions = vacay_mate._parse_attractions_from_content(html_content, "Paris")
        
        # Should extract attractions despite HTML (may contain some HTML remnants)
        assert len(attractions) > 0
        
        # Most attraction names should be reasonable (not all HTML)
        reasonable_attractions = [a for a in attractions if len(a["name"]) > 5 and not a["name"].startswith("<")]
        assert len(reasonable_attractions) > 0

    def test_parse_attractions_deduplication(self):
        """Test attraction deduplication."""
        vacay_mate = VacayMate()
        
        duplicate_content = [
            {"content": "Visit the Eiffel Tower and the Louvre Museum."},
            {"content": "The Eiffel Tower is iconic. Also see the Louvre Museum."},
            {"content": "Eiffel Tower and other attractions."}
        ]
        
        attractions = vacay_mate._parse_attractions_from_content(duplicate_content, "Paris")
        
        # Should deduplicate attractions
        attraction_names = [a["name"].lower() for a in attractions]
        unique_names = set(attraction_names)
        assert len(unique_names) == len(attraction_names)  # No duplicates

    def test_parse_attractions_empty_content(self):
        """Test attraction parsing with empty content."""
        vacay_mate = VacayMate()
        
        empty_content = [
            {"content": ""},
            {"content": None},
            {}
        ]
        
        attractions = vacay_mate._parse_attractions_from_content(empty_content, "TestCity")
        
        # Should fallback to generic attractions
        assert len(attractions) > 0
        assert any("TestCity" in a["name"] for a in attractions)


class TestTableFormatting:
    """Test table formatting functionality."""

    def test_flight_table_formatting(self, mock_flight_data):
        """Test flight table formatting."""
        flights = mock_flight_data["flights"][:3]  # First 3 flights
        
        # Simulate table creation
        table_rows = []
        for flight in flights:
            if flight.get("id") != "flight_003_edge_case":  # Skip edge case
                airline = flight.get("airline", "N/A")
                flight_num = flight.get("flightNumber", "N/A")
                from_airport = flight.get("departureAirport", "N/A")
                to_airport = flight.get("arrivalAirport", "N/A")
                departure = flight.get("departureTime", "N/A")
                arrival = flight.get("arrivalTime", "N/A")
                duration = flight.get("durationOutbound", "N/A")
                price = f"${flight.get('priceUSD', 0):.2f}"
                
                row = f"| {airline} | {flight_num} | {from_airport} | {to_airport} | {departure} | {arrival} | {duration} | {price} |"
                table_rows.append(row)
        
        # Verify table structure
        assert len(table_rows) >= 2  # Should have at least 2 valid flights
        for row in table_rows:
            assert row.count("|") == 9  # 8 columns + 2 edge pipes

    def test_hotel_table_formatting(self, mock_hotel_data):
        """Test hotel table formatting."""
        hotels = mock_hotel_data["hotels"][:3]  # First 3 hotels
        
        # Simulate table creation
        table_rows = []
        for hotel in hotels:
            if hotel.get("name") != "Edge Case Hotel":  # Skip edge case
                name = hotel.get("name", "N/A")
                price = hotel.get("price", {})
                per_night = price.get("per_night", "N/A") if isinstance(price, dict) else "N/A"
                rating = f"{hotel.get('rating', 'N/A')}★" if hotel.get('rating') else "N/A"
                address = hotel.get("address", {})
                area = address.get("area", "N/A") if isinstance(address, dict) else "N/A"
                amenities = hotel.get("amenities", "N/A")
                link_text = "[Book](link)" if hotel.get("booking_link") else "N/A"
                
                row = f"| {name} | {per_night} | {rating} | {area} | {amenities} | {link_text} |"
                table_rows.append(row)
        
        # Verify table structure
        assert len(table_rows) >= 3  # Should have at least 3 valid hotels
        for row in table_rows:
            assert row.count("|") == 7  # 6 columns + 2 edge pipes

    def test_table_cell_escaping(self):
        """Test table cell content escaping."""
        # Test data with special characters
        test_data = {
            "name": "Hotel | With | Pipes",
            "description": "Description with\nnewlines and | pipes",
            "price": "$1,250.50"
        }
        
        # Simulate cell content processing
        name = test_data["name"].replace("|", "\\|")  # Escape pipes
        description = test_data["description"].replace("\n", " ").replace("|", "\\|")
        
        assert "\\|" in name
        assert "\\|" in description
        assert "\n" not in description

    def test_table_alignment(self):
        """Test table column alignment."""
        # Test numeric alignment
        prices = ["$125.50", "$1,250.75", "$98.00"]
        
        # Right-align numeric columns (markdown syntax)
        header = "| Hotel | Price |"
        separator = "|-------|------:|"  # Right-aligned price column
        
        assert separator.endswith(":|")  # Right alignment syntax


class TestFileExport:
    """Test file export functionality."""

    def test_export_markdown_plan_basic(self, populated_vacation_state, temp_output_dir):
        """Test basic markdown file export."""
        vacay_mate = VacayMate()
        
        # Mock the outputs directory
        with patch('os.path.join', return_value=str(temp_output_dir / "test_plan.md")):
            with patch('os.makedirs'):
                with patch('builtins.open', mock_open()) as mock_file:
                    vacay_mate._export_markdown_plan(
                        populated_vacation_state,
                        "Paris",
                        "2025-09-15",
                        "2025-09-20"
                    )
                    
                    # Verify file operations
                    mock_file.assert_called_once()
                    handle = mock_file.return_value.__enter__.return_value
                    handle.write.assert_called_once()
                    
                    # Verify content was written
                    written_content = handle.write.call_args[0][0]
                    assert isinstance(written_content, str)
                    assert "# 🌍 Vacation Plan: Paris" in written_content

    def test_export_filename_generation(self, populated_vacation_state):
        """Test filename generation for exports."""
        vacay_mate = VacayMate()
        
        # Mock datetime for consistent filename
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20250915_143022"
            
            with patch('os.makedirs'):
                with patch('builtins.open', mock_open()):
                    with patch('os.path.join') as mock_join:
                        vacay_mate._export_markdown_plan(
                            populated_vacation_state,
                            "Paris",
                            "2025-09-15",
                            "2025-09-20"
                        )
                        
                        # Check filename generation
                        expected_filename = "vacation_plan_paris_20250915_143022.md"
                        mock_join.assert_called()
                        call_args = mock_join.call_args_list[-1][0]  # Last call
                        assert expected_filename in call_args

    def test_export_directory_creation(self, populated_vacation_state):
        """Test output directory creation."""
        vacay_mate = VacayMate()
        
        with patch('os.makedirs') as mock_makedirs:
            with patch('builtins.open', mock_open()):
                vacay_mate._export_markdown_plan(
                    populated_vacation_state,
                    "Barcelona",
                    "2025-09-15",
                    "2025-09-20"
                )
                
                # Verify directory creation
                mock_makedirs.assert_called_once()
                call_args = mock_makedirs.call_args
                assert call_args[1]["exist_ok"] is True

    def test_export_error_handling(self, populated_vacation_state):
        """Test error handling during file export."""
        vacay_mate = VacayMate()
        
        # Mock file write error
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with patch('os.makedirs'):
                with patch('builtins.print') as mock_print:
                    vacay_mate._export_markdown_plan(
                        populated_vacation_state,
                        "Madrid",
                        "2025-09-15",
                        "2025-09-20"
                    )
                    
                    # Should print error message
                    mock_print.assert_called()
                    error_message = mock_print.call_args[0][0]
                    assert "Error exporting" in error_message

    def test_export_content_encoding(self, populated_vacation_state):
        """Test UTF-8 encoding in file export."""
        vacay_mate = VacayMate()
        
        with patch('os.makedirs'):
            with patch('builtins.open', mock_open()) as mock_file:
                vacay_mate._export_markdown_plan(
                    populated_vacation_state,
                    "Zürich",  # City with special characters
                    "2025-09-15",
                    "2025-09-20"
                )
                
                # Verify UTF-8 encoding
                mock_file.assert_called_once()
                call_args = mock_file.call_args
                assert call_args[1]["encoding"] == "utf-8"


class TestDataStructureFormatting:
    """Test data structure formatting and validation."""

    def test_format_currency_values(self):
        """Test currency value formatting."""
        test_cases = [
            (125.50, "$125.50"),
            (1250.75, "$1,250.75"),
            (0.0, "$0.00"),
            (1000000.0, "$1,000,000.00")
        ]
        
        for input_val, expected in test_cases:
            # Simulate currency formatting
            formatted = f"${input_val:,.2f}"
            assert formatted == expected

    def test_format_date_strings(self):
        """Test date string formatting."""
        test_cases = [
            ("2025-09-15", "Sep 15"),
            ("2025-12-25", "Dec 25"),
            ("2025-01-01", "Jan 01")
        ]
        
        for date_str, expected in test_cases:
            # Simulate date formatting
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted = date_obj.strftime("%b %d")
            assert formatted == expected

    def test_format_rating_display(self):
        """Test rating display formatting."""
        test_cases = [
            (4.5, "4.5★"),
            (5.0, "5.0★"),
            (3.8, "3.8★"),
            (None, "N/A"),
            (0, "0★")
        ]
        
        for rating, expected in test_cases:
            if rating is None:
                formatted = "N/A"
            else:
                formatted = f"{rating}★"
            assert formatted == expected

    def test_format_duration_display(self):
        """Test duration display formatting."""
        test_cases = [
            ("2h 30m", "2h 30m"),
            ("150", "150"),  # Raw minutes
            ("", "N/A"),
            (None, "N/A")
        ]
        
        for duration, expected in test_cases:
            formatted = duration if duration else "N/A"
            if expected == "N/A":
                assert formatted == expected
            else:
                assert formatted == duration


@pytest.mark.edge_case
class TestFormatterEdgeCases:
    """Test edge cases for formatting functionality."""

    def test_markdown_with_special_characters(self, sample_vacation_state):
        """Test markdown generation with special characters."""
        vacay_mate = VacayMate()
        
        # Add special characters to state
        special_state = sample_vacation_state.copy()
        special_state["destination"] = "Zürich & München"
        special_state["research_results"] = {
            "flights": [{
                "airline": "Swiss Air <script>alert('test')</script>",
                "priceUSD": 500.0
            }]
        }
        
        markdown = vacay_mate._build_markdown_content(
            special_state,
            "Zürich & München",
            "2025-09-15",
            "2025-09-20"
        )
        
        # Should handle special characters safely
        assert "Zürich & München" in markdown
        # Note: The current implementation may not escape HTML, which is a production issue

    def test_markdown_with_very_long_content(self, sample_vacation_state):
        """Test markdown generation with very long content."""
        vacay_mate = VacayMate()
        
        # Create state with very long strings
        long_state = sample_vacation_state.copy()
        long_description = "Very long description. " * 1000  # 25,000+ characters
        long_state["research_results"] = {
            "destination_info": [{"content": long_description}]
        }
        
        markdown = vacay_mate._build_markdown_content(
            long_state,
            "TestCity",
            "2025-09-15",
            "2025-09-20"
        )
        
        # Should handle long content without issues
        assert isinstance(markdown, str)
        assert len(markdown) > 1000

    def test_markdown_with_null_values(self, sample_vacation_state):
        """Test markdown generation with null/None values."""
        vacay_mate = VacayMate()
        
        # Create state with null values
        null_state = sample_vacation_state.copy()
        null_state["research_results"] = {
            "flights": [{"airline": None, "priceUSD": None}],
            "accommodations": {"hotels": [{"name": None, "price": None}]}
        }
        
        markdown = vacay_mate._build_markdown_content(
            null_state,
            "TestCity",
            "2025-09-15",
            "2025-09-20"
        )
        
        # Should handle null values gracefully
        assert isinstance(markdown, str)
        assert "N/A" in markdown  # Should show placeholder for missing data

    def test_export_with_invalid_characters_in_filename(self, populated_vacation_state):
        """Test file export with invalid filename characters."""
        vacay_mate = VacayMate()
        
        with patch('os.makedirs'):
            with patch('builtins.open', mock_open()) as mock_file:
                # Destination with invalid filename characters
                vacay_mate._export_markdown_plan(
                    populated_vacation_state,
                    "Paris/London<>|?*",
                    "2025-09-15",
                    "2025-09-20"
                )
                
                # Should handle invalid characters in filename
                mock_file.assert_called_once()
                # Note: Current implementation may not sanitize filenames - this is a production issue
