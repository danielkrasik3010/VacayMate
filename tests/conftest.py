"""
Pytest configuration and shared fixtures for VacayMate test suite.

This file contains:
- Mock data fixtures for flights, hotels, events, weather
- Mock API client fixtures 
- Common test utilities and helpers
- Pytest configuration settings
"""

import pytest
import json
import os
from datetime import datetime, date, timedelta
from unittest.mock import Mock
from pydantic import BaseModel

# Import VacayMate components for testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from states.VacayMate_state import VacationPlannerState, initialize_vacation_state
from consts import MANAGER, RESEARCHER, CALCULATOR, PLANNER, SUMMARIZER


# ================ FIXTURE DATA LOADERS ================

@pytest.fixture
def mock_flight_data():
    """Load mock flight data from JSON fixture."""
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'mock_flights.json')
    with open(fixture_path, 'r') as f:
        return json.load(f)

@pytest.fixture  
def mock_hotel_data():
    """Load mock hotel data from JSON fixture."""
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'mock_hotels.json')
    with open(fixture_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def mock_event_data():
    """Load mock event data from JSON fixture."""
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'mock_events.json')
    with open(fixture_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def mock_weather_data():
    """Mock weather forecast data."""
    return {
        "forecasts": [
            {
                "date": "2025-09-15",
                "condition": "partly cloudy",
                "temp_high": 22.5,
                "temp_low": 15.2,
                "wind_speed": 12.3,
                "humidity": 65,
                "precipitation": 0.0
            },
            {
                "date": "2025-09-16", 
                "condition": "sunny",
                "temp_high": 25.1,
                "temp_low": 16.8,
                "wind_speed": 8.7,
                "humidity": 58,
                "precipitation": 0.0
            },
            {
                "date": "2025-09-17",
                "condition": "light rain",
                "temp_high": 19.4,
                "temp_low": 13.6,
                "wind_speed": 15.2,
                "humidity": 78,
                "precipitation": 2.3
            }
        ],
        "human_readable_summary": "Expect partly cloudy conditions on Sep 15 with highs of 22.5° and lows of 15.2°. Sunny weather on Sep 16 with highs of 25.1°. Light rain expected on Sep 17."
    }

@pytest.fixture
def mock_destination_info():
    """Mock destination research data."""
    return [
        {
            "url": "https://example.com/paris-attractions",
            "content": "Paris, the City of Light, offers numerous attractions. The Eiffel Tower stands as the iconic symbol of Paris. The Louvre Museum houses the famous Mona Lisa. Notre-Dame Cathedral showcases Gothic architecture. Arc de Triomphe marks the Champs-Élysées. Montmartre district features Sacré-Cœur Basilica."
        },
        {
            "url": "https://example.com/paris-restaurants", 
            "content": "Paris dining scene includes Michelin-starred restaurants, traditional bistros, and charming cafés. The Latin Quarter offers authentic French cuisine. Le Marais district has trendy eateries."
        }
    ]


# ================ MOCK API CLIENTS ================

@pytest.fixture
def mock_groq_client():
    """Mock Groq client for LLM calls."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "120"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

@pytest.fixture
def mock_serpapi_client():
    """Mock SerpAPI client for hotel/event searches."""
    mock_client = Mock()
    return mock_client

@pytest.fixture
def mock_owm_client():
    """Mock OpenWeatherMap client."""
    mock_client = Mock()
    return mock_client

@pytest.fixture
def mock_tavily_client():
    """Mock Tavily client for destination research."""
    mock_client = Mock()
    return mock_client

@pytest.fixture
def mock_rapidapi_client():
    """Mock RapidAPI client for flight searches."""
    mock_client = Mock()
    return mock_client


# ================ STATE FIXTURES ================

@pytest.fixture
def sample_vacation_state():
    """Sample VacationPlannerState for testing."""
    return initialize_vacation_state(
        user_request="Plan a 5-day trip to Paris",
        current_location="Barcelona",
        destination="Paris",
        start_date="2025-09-15",
        return_date="2025-09-20"
    )

@pytest.fixture
def populated_vacation_state(sample_vacation_state, mock_flight_data, mock_hotel_data, mock_event_data, mock_weather_data):
    """VacationPlannerState populated with mock research data."""
    state = sample_vacation_state.copy()
    
    # Add research results
    state["research_results"] = {
        "flights": mock_flight_data["flights"],
        "accommodations": {
            "query": "Paris",
            "check_in_date": "2025-09-15",
            "check_out_date": "2025-09-20", 
            "total_found": len(mock_hotel_data["hotels"]),
            "hotels": mock_hotel_data["hotels"]
        },
        "destination_info": [
            {"content": "Paris attractions include Eiffel Tower, Louvre Museum, Notre-Dame Cathedral."}
        ]
    }
    
    # Add planner results
    state["planner_results"] = {
        "weather_forecast": mock_weather_data,
        "local_events": mock_event_data["events"]
    }
    
    # Add calculator results
    state["calculator_results"] = {
        "days": 5,
        "hotel_total": 750.00,
        "flight_total": 350.00,
        "daily_cost_estimate": 120.00,
        "daily_total": 600.00,
        "subtotal": 1700.00,
        "commission_rate": 0.1,
        "commission_amount": 170.00,
        "final_quotation": 1870.00
    }
    
    return state


# ================ DATE AND TIME FIXTURES ================

@pytest.fixture
def sample_dates():
    """Sample date ranges for testing."""
    return {
        "start_date": "2025-09-15",
        "end_date": "2025-09-20", 
        "start_date_obj": date(2025, 9, 15),
        "end_date_obj": date(2025, 9, 20),
        "days": 5
    }

@pytest.fixture
def edge_case_dates():
    """Edge case dates for testing."""
    return {
        "same_day": {
            "start": "2025-09-15",
            "end": "2025-09-15",
            "days": 0
        },
        "one_day": {
            "start": "2025-09-15", 
            "end": "2025-09-16",
            "days": 1
        },
        "long_trip": {
            "start": "2025-09-15",
            "end": "2025-10-15", 
            "days": 30
        },
        "past_dates": {
            "start": "2024-01-01",
            "end": "2024-01-05",
            "days": 4
        }
    }


# ================ PRICE FIXTURES ================

@pytest.fixture
def sample_prices():
    """Sample price data for testing calculations."""
    return {
        "hotel_prices": [120.50, 135.00, 98.75, 156.25, 142.00],
        "flight_prices": [285.50, 312.00, 298.75, 276.50],
        "daily_costs": [85.00, 120.00, 150.00, 95.00, 110.00]
    }

@pytest.fixture
def edge_case_prices():
    """Edge case price data for testing."""
    return {
        "zero_prices": {
            "hotels": [0.0, 0.0, 0.0],
            "flights": [0.0, 0.0]
        },
        "negative_prices": {
            "hotels": [-50.0, 100.0, 150.0],
            "flights": [200.0, -25.0]
        },
        "very_high_prices": {
            "hotels": [5000.0, 10000.0, 15000.0],
            "flights": [25000.0, 30000.0]
        },
        "single_prices": {
            "hotels": [125.0],
            "flights": [300.0]
        },
        "string_prices": {
            "hotels": ["125.50", "98.75", "156.00"],
            "flights": ["285.00", "312.50"]
        }
    }


# ================ UTILITY FIXTURES ================

@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for output file testing."""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir

@pytest.fixture 
def mock_environment_variables():
    """Mock environment variables for API keys."""
    return {
        "OPENAI_API_KEY": "mock-openai-key",
        "GROQ_API_KEY": "mock-groq-key", 
        "TAVILY_API_KEY": "mock-tavily-key",
        "SERPAPI_API_KEY": "mock-serpapi-key",
        "RAPIDAPI_KEY": "mock-rapidapi-key",
        "OPENWEATHER_API_KEY": "mock-weather-key"
    }


# ================ PYTEST CONFIGURATION ================

def pytest_configure(config):
    """Pytest configuration setup."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "edge_case: mark test as an edge case test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

@pytest.fixture(autouse=True)
def mock_env_vars(mock_environment_variables, monkeypatch):
    """Automatically mock environment variables for all tests."""
    for key, value in mock_environment_variables.items():
        monkeypatch.setenv(key, value)


# ================ HELPER FUNCTIONS ================

def assert_valid_price(price):
    """Helper function to assert price validity."""
    assert isinstance(price, (int, float))
    assert price >= 0
    assert not (isinstance(price, float) and (price != price))  # Check for NaN

def assert_valid_date_string(date_str):
    """Helper function to assert date string format."""
    assert isinstance(date_str, str)
    datetime.strptime(date_str, "%Y-%m-%d")  # Will raise if invalid format

def assert_valid_state_structure(state):
    """Helper function to validate state structure."""
    required_keys = [
        "user_request", "current_location", "destination", 
        "start_date", "return_date", "research_results",
        "calculator_results", "planner_results"
    ]
    for key in required_keys:
        assert key in state, f"Missing required state key: {key}"
