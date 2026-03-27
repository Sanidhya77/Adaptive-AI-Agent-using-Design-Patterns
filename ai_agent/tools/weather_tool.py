"""Weather tool implementation using Open-Meteo."""

from __future__ import annotations

from typing import Any

import requests

from tools.base_tool import BaseTool


class WeatherTool(BaseTool):
    """Concrete Strategy - fetches live weather using Open-Meteo (no API key)."""

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    def execute(self, city: str) -> str:
        """Fetch the current weather for a city using the Open-Meteo APIs.

        Args:
            city: The city name to look up.

        Returns:
            A human-readable weather summary or a helpful error message.
        """
        geocoding_url = (
            "https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city}&count=1&language=en&format=json"
        )
        try:
            geocoding_response = requests.get(geocoding_url, timeout=10)
            geocoding_response.raise_for_status()
            geocoding_data = geocoding_response.json()
        except requests.exceptions.ConnectionError:
            return "Connection error while contacting geocoding service."
        except requests.exceptions.Timeout:
            return "Weather service timed out while geocoding the city."
        except requests.exceptions.RequestException as error:
            return f"Weather geocoding request failed: {error}"

        results = geocoding_data.get("results")
        if not results:
            return f"City '{city}' not found. Try a different spelling."

        location = results[0]
        latitude = location["latitude"]
        longitude = location["longitude"]
        country = location.get("country", "")

        weather_url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}&current_weather=true"
        )
        try:
            weather_response = requests.get(weather_url, timeout=10)
            weather_response.raise_for_status()
            weather_data = weather_response.json()
        except requests.exceptions.ConnectionError:
            return "Connection error while contacting weather service."
        except requests.exceptions.Timeout:
            return "Weather service timed out while retrieving forecast data."
        except requests.exceptions.RequestException as error:
            return f"Weather forecast request failed: {error}"

        current_weather = weather_data.get("current_weather")
        if not current_weather:
            return f"Weather data unavailable for '{city}'."

        temperature = current_weather["temperature"]
        windspeed = current_weather["windspeed"]
        return f"Weather in {city}, {country}: {temperature}°C, wind {windspeed} km/h"

    def get_declaration(self) -> dict[str, Any]:
        """Return the Gemini function declaration for this tool.

        Returns:
            A JSON-schema-compatible declaration for weather lookup.
        """
        return {
            "name": "get_weather",
            "description": (
                "Gets current weather for any city. Use when user asks about "
                "weather, temperature, or conditions in a location."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name to look up weather for.",
                    }
                },
                "required": ["city"],
            },
        }
