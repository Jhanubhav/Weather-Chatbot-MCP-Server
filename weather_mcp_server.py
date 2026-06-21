import httpx
import json
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP weather server - now global!
mcp = FastMCP("Global Weather Server")

# Mapping of WMO Weather Interpretation Codes (WMO) to descriptions
WMO_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

@mcp.tool()
async def get_city_weather(city: str) -> str:
    """
    Fetch the current temperature and weather conditions for ANY city in the world.

    Args:
        city: The name of the city anywhere in the world (e.g. "Delhi", "Paris", "New York", "Tokyo").
    """
    if not city or not city.strip():
        return json.dumps({"error": "City name cannot be empty."})

    city_name = city.strip()

    # 1. Geocode the city name globally using Open-Meteo Geocoding API
    geocode_url = (
        f"https://geocoding-api.open-meteo.com/v1/search"
        f"?name={city_name}&count=5&language=en&format=json"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            geo_response = await client.get(geocode_url)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            results = geo_data.get("results", [])
            if not results:
                return json.dumps({
                    "error": f"Could not find any city matching '{city_name}'. Please check the spelling and try again.",
                    "code": "CITY_NOT_FOUND"
                })

            # Pick the top (best) result
            best = results[0]
            lat = best.get("latitude")
            lon = best.get("longitude")
            resolved_name = best.get("name", city_name)
            state = best.get("admin1", "")
            country = best.get("country", "")
            country_code = best.get("country_code", "")

            # 2. Fetch weather using auto timezone so local time is correct
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
                f"is_day,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m"
                f"&timezone=auto"
            )

            weather_response = await client.get(weather_url)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            current = weather_data.get("current", {})

            # 3. Format the result
            weather_code = current.get("weather_code", 0)
            weather_desc = WMO_DESCRIPTIONS.get(weather_code, "Unknown weather condition")

            output = {
                "success": True,
                "city": resolved_name,
                "state": state,
                "country": country,
                "country_code": country_code,
                "latitude": lat,
                "longitude": lon,
                "temperature": current.get("temperature_2m"),
                "apparent_temperature": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "is_day": current.get("is_day") == 1,
                "weather_code": weather_code,
                "weather_description": weather_desc,
                "time": current.get("time"),
                "timezone": weather_data.get("timezone", "")
            }

            return json.dumps(output)

    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP error occurred: {e}", "code": "HTTP_ERROR"})
    except httpx.RequestError as e:
        return json.dumps({"error": f"Network error occurred: {e}", "code": "NETWORK_ERROR"})
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}", "code": "UNEXPECTED_ERROR"})

if __name__ == "__main__":
    mcp.run(transport="stdio")
