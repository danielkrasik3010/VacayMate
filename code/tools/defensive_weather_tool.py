"""
Defensive Weather Forecast Tool

Enhanced version of the weather forecast tool with defensive programming patterns:
- Circuit breaker protection
- Exponential backoff retry logic
- Output validation with Pydantic
- Resource limits
- Comprehensive error handling
"""


import json
from datetime import datetime, timedelta
import sys
from typing import Dict, Any
from langchain.agents import tool
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

# Import defensive patterns
from defensive_patterns import (
    safe_api_call, 
    weather_fallback, 
    ValidatedWeatherResponse,
    retry_with_backoff,
    resource_limited
)

# Add utils to path for secrets manager
utils_dir = current_dir.parent / "utils"
sys.path.insert(0, str(utils_dir))

from secrets_manager import get_secret

# Import OWM with fallback
try:
    from pyowm import OWM
    OWM_AVAILABLE = True
except ImportError:
    OWM_AVAILABLE = False
    print("Warning: pyowm not available, weather tool will use fallback data")

OWM_API_KEY = get_secret('OWM_API_KEY', 'owm')

@resource_limited(max_memory_mb=100, max_time_seconds=30)
@retry_with_backoff(max_retries=3, base_delay=1.0)
def _fetch_weather_data(location: str, days: int = 5, units: str = "metric") -> Dict[str, Any]:
    """
    Internal function to fetch weather data with defensive patterns.
    
    This function is wrapped with resource limits and retry logic.
    """
    # Validate inputs
    if not location or not location.strip():
        raise ValueError("Location parameter is required and cannot be empty")
    
    if days < 1 or days > 14:
        raise ValueError("Days must be between 1 and 14")
    
    if units not in ["metric", "imperial"]:
        raise ValueError("Units must be 'metric' or 'imperial'")
    
    # Check if OWM is available
    if not OWM_AVAILABLE:
        raise ImportError("OpenWeatherMap library (pyowm) is not available")
    
    # Validate API key
    if not OWM_API_KEY or OWM_API_KEY == "your_owm_api_key_here":
        raise ValueError("OWM_API_KEY is not properly configured")
    
    # Initialize OWM client
    try:
        owm = OWM(OWM_API_KEY)
        mgr = owm.weather_manager()
    except Exception as e:
        raise ConnectionError(f"Failed to initialize OpenWeatherMap client: {e}")
    
    # Fetch forecast data
    try:
        forecast = mgr.forecast_at_place(location, '3h')
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            raise ValueError(f"Location '{location}' not found")
        elif "401" in str(e) or "unauthorized" in str(e).lower():
            raise ValueError("Invalid OpenWeatherMap API key")
        elif "429" in str(e) or "quota" in str(e).lower():
            raise Exception("OpenWeatherMap API quota exceeded")
        else:
            raise Exception(f"Weather API error: {e}")
    
    # Process forecast data
    daily_forecasts = {}
    
    for weather in forecast.forecast:
        try:
            date_str = weather.reference_time('iso').split(' ')[0]
            temp_unit = 'celsius' if units == "metric" else 'fahrenheit'
            temp = weather.temperature(temp_unit)['temp']
            
            # Initialize or update daily forecast
            if date_str not in daily_forecasts:
                daily_forecasts[date_str] = {
                    "condition": weather.detailed_status or "Unknown",
                    "temp_high": temp,
                    "temp_low": temp,
                    "wind_speed": weather.wind().get('speed', 0) if weather.wind() else 0,
                    "humidity": weather.humidity or 0,
                    "precipitation": weather.rain.get('3h', 0) if weather.rain else 0
                }
            else:
                # Update temperature extremes
                daily_forecasts[date_str]['temp_high'] = max(daily_forecasts[date_str]['temp_high'], temp)
                daily_forecasts[date_str]['temp_low'] = min(daily_forecasts[date_str]['temp_low'], temp)
                
                # Update precipitation (sum for the day)
                precip = weather.rain.get('3h', 0) if weather.rain else 0
                daily_forecasts[date_str]['precipitation'] += precip
                
        except Exception as e:
            # Log individual weather entry errors but continue processing
            print(f"Warning: Error processing weather entry: {e}")
            continue
    
    # Limit to requested number of days
    output_list = list(daily_forecasts.items())[:days]
    
    if not output_list:
        raise Exception("No weather data could be processed")
    
    # Build simplified forecasts
    simplified_forecasts = []
    summary_lines = []
    
    for date_str, info in output_list:
        # Round temperatures to 1 decimal place
        temp_high = round(info['temp_high'], 1)
        temp_low = round(info['temp_low'], 1)
        wind_speed = round(info['wind_speed'], 1) if info['wind_speed'] else 0
        precipitation = round(info['precipitation'], 2)
        
        forecast_entry = {
            "date": date_str,
            "condition": info['condition'],
            "temp_high": temp_high,
            "temp_low": temp_low,
            "wind_speed": wind_speed,
            "humidity": info['humidity'],
            "precipitation": precipitation
        }
        simplified_forecasts.append(forecast_entry)
        
        # Build human-readable summary
        unit_symbol = "°C" if units == "metric" else "°F"
        wind_unit = "m/s" if units == "metric" else "mph"
        precip_unit = "mm" if units == "metric" else "in"
        
        summary_lines.append(
            f"On {date_str}, expect {info['condition']} with highs of {temp_high}{unit_symbol} "
            f"and lows of {temp_low}{unit_symbol}. Wind: {wind_speed} {wind_unit}, "
            f"Humidity: {info['humidity']}%, Precipitation: {precipitation} {precip_unit}."
        )
    
    return {
        "forecasts": simplified_forecasts,
        "human_readable_summary": " ".join(summary_lines),
        "debug": {
            "location": location,
            "days_requested": days,
            "days_returned": len(simplified_forecasts),
            "units": units,
            "timestamp": datetime.now().isoformat()
        }
    }

@tool
def get_weather_forecast_defensive(location: str, days: int = 5, units: str = "metric") -> Dict[str, Any]:
    """
    Defensive weather forecast tool with circuit breaker, retry logic, and validation.
    
    This tool automatically handles:
    - API failures with exponential backoff
    - Circuit breaker protection against repeated failures
    - Input validation and sanitization
    - Output validation with Pydantic models
    - Resource usage limits
    - Comprehensive error logging
    
    Args:
        location: City or location name for weather forecast
        days: Number of days to forecast (1-14, defaults to 5)
        units: Temperature units - 'metric' (Celsius) or 'imperial' (Fahrenheit)
    
    Returns:
        Dict: Validated weather forecast results with fallback data if needed
    """
    def weather_api_call():
        return _fetch_weather_data(
            location=location,
            days=days,
            units=units
        )
    
    def enhanced_fallback():
        return weather_fallback(
            location=location,
            days=days,
            units=units
        )
    
    # Use safe API call with circuit breaker protection
    result = safe_api_call(
        tool_name="weather_forecast",
        api_func=weather_api_call,
        fallback_func=enhanced_fallback
    )
    
    # Validate the result using Pydantic
    try:
        validated_result = ValidatedWeatherResponse(**result)
        return validated_result.dict()
    except Exception as e:
        # If validation fails, return a safe fallback
        return ValidatedWeatherResponse(
            forecasts=[],
            human_readable_summary=f"Weather forecast for {location} is currently unavailable due to validation error: {str(e)}",
            error=f"Response validation failed: {str(e)}"
        ).dict()

# Backward compatibility - alias to the original function name
get_weather_forecast = get_weather_forecast_defensive

# Enhanced fallback with realistic weather data
def generate_fallback_weather(location: str, days: int = 5, units: str = "metric") -> Dict[str, Any]:
    """Generate realistic fallback weather data when API is unavailable."""
    import random
    
    # Common weather conditions
    conditions = [
        "partly cloudy", "sunny", "cloudy", "light rain", 
        "overcast", "clear sky", "scattered clouds"
    ]
    
    # Temperature ranges by season (rough approximation)
    today = datetime.now().date()
    month = today.month
    
    if units == "metric":
        if month in [12, 1, 2]:  # Winter
            temp_range = (0, 10)
        elif month in [3, 4, 5]:  # Spring
            temp_range = (10, 20)
        elif month in [6, 7, 8]:  # Summer
            temp_range = (20, 30)
        else:  # Fall
            temp_range = (5, 15)
        unit_symbol = "°C"
        wind_unit = "m/s"
        precip_unit = "mm"
    else:
        if month in [12, 1, 2]:  # Winter
            temp_range = (32, 50)
        elif month in [3, 4, 5]:  # Spring
            temp_range = (50, 68)
        elif month in [6, 7, 8]:  # Summer
            temp_range = (68, 86)
        else:  # Fall
            temp_range = (41, 59)
        unit_symbol = "°F"
        wind_unit = "mph"
        precip_unit = "in"
    
    forecasts = []
    summary_lines = []
    
    for i in range(days):
        forecast_date = today + timedelta(days=i)
        date_str = forecast_date.isoformat()
        
        condition = random.choice(conditions)
        temp_high = random.randint(temp_range[0] + 5, temp_range[1] + 5)
        temp_low = random.randint(temp_range[0], temp_range[1] - 5)
        wind_speed = round(random.uniform(0, 15), 1)
        humidity = random.randint(30, 90)
        precipitation = round(random.uniform(0, 5), 2) if "rain" in condition else 0
        
        forecast_entry = {
            "date": date_str,
            "condition": condition,
            "temp_high": temp_high,
            "temp_low": temp_low,
            "wind_speed": wind_speed,
            "humidity": humidity,
            "precipitation": precipitation
        }
        forecasts.append(forecast_entry)
        
        summary_lines.append(
            f"On {date_str}, expect {condition} with highs of {temp_high}{unit_symbol} "
            f"and lows of {temp_low}{unit_symbol}. Wind: {wind_speed} {wind_unit}, "
            f"Humidity: {humidity}%, Precipitation: {precipitation} {precip_unit}."
        )
    
    return {
        "forecasts": forecasts,
        "human_readable_summary": f"Fallback weather forecast for {location}: " + " ".join(summary_lines),
        "error": "Using fallback weather data - actual weather service unavailable"
    }

# Test function
if __name__ == "__main__":
    print("Testing defensive weather forecast tool...")
    
    test_params = {
        "location": "London",
        "days": 5,
        "units": "metric"
    }
    
    result = get_weather_forecast_defensive.invoke(test_params)
    print(json.dumps(result, indent=2, default=str))
    
    # Test fallback data generation
    print("\nTesting fallback weather data...")
    fallback_result = generate_fallback_weather("Paris", 3, "metric")
    print(json.dumps(fallback_result, indent=2, default=str))
    
    # Test circuit breaker status
    from defensive_patterns import get_system_health
    print("\nSystem health:", json.dumps(get_system_health(), indent=2, default=str))

