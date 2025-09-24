import os
import json
from datetime import datetime, timedelta, date
import sys
from pyowm import OWM
from langchain.agents import tool
from pathlib import Path

# Add utils to path for secrets manager
current_dir = Path(__file__).parent
utils_dir = current_dir.parent / "utils"
sys.path.insert(0, str(utils_dir))

from secrets_manager import get_secret

# API keys are loaded from environment variables via .env file
OWM_API_KEY = get_secret('OWM_API_KEY', 'owm')

# ========================================================================
#   WEATHER FORECAST TOOL (with human-readable summary)
# ========================================================================

@tool
def get_weather_forecast(location: str, days: int = 5, units: str = "metric") -> str:
    """
    Retrieves daily weather forecasts for the next 'days' days.
    Returns date, condition, temp_high, temp_low, wind, humidity, precipitation.
    Also provides a human-readable summary.
    """
    try:
        owm = OWM(OWM_API_KEY)
        mgr = owm.weather_manager()
        forecast = mgr.forecast_at_place(location, '3h')

        daily_forecasts = {}
        for weather in forecast.forecast:
            date_str = weather.reference_time('iso').split(' ')[0]
            temp = weather.temperature('celsius' if units=="metric" else 'fahrenheit')['temp']
            daily_forecasts.setdefault(date_str, {
                "condition": weather.detailed_status,
                "temp_high": temp,
                "temp_low": temp,
                "wind_speed": weather.wind().get('speed'),
                "humidity": weather.humidity,
                "precipitation": weather.rain.get('3h', 0) if weather.rain else 0
            })
            daily_forecasts[date_str]['temp_high'] = max(daily_forecasts[date_str]['temp_high'], temp)
            daily_forecasts[date_str]['temp_low'] = min(daily_forecasts[date_str]['temp_low'], temp)

        output_list = list(daily_forecasts.items())[:days]

        # Human-readable summary
        summary_lines = []
        simplified_forecasts = []
        for date_str, info in output_list:
            simplified_forecasts.append({
                "date": date_str,
                "condition": info['condition'],
                "temp_high": info['temp_high'],
                "temp_low": info['temp_low'],
                "wind_speed": info['wind_speed'],
                "humidity": info['humidity'],
                "precipitation": info['precipitation']
            })
            summary_lines.append(
                f"On {date_str}, expect {info['condition']} with highs of {info['temp_high']}° and lows of {info['temp_low']}°. "
                f"Wind: {info['wind_speed']} units, Humidity: {info['humidity']}%, Precipitation: {info['precipitation']} units."
            )

        return {
            "forecasts": simplified_forecasts,
            "human_readable_summary": " ".join(summary_lines)
        }

    except Exception as e:
        return {
            "forecasts": [],
            "human_readable_summary": f"Error with Weather Forecast Tool: {e}"
        }

# ========================================================================
# 5. TESTING THE TOOLS
# ========================================================================

if __name__ == "__main__":
    today = date.today()
    next_week = today + timedelta(days=7)
    print("Testing Weather Forecast Tool...")
    weather_result = get_weather_forecast.invoke({
        "location": "London",
        "days": 5,
        "units": "metric"
    })
    print(weather_result)
    print("\n---------------------------------------")