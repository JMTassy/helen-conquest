import requests
from typing import Dict, Any, Optional

class WeatherService:
    @staticmethod
    def get_weather(location: str = "London") -> Dict[str, Any]:
        """
        Fetch weather from wttr.in.
        """
        try:
            # Using format strings as per WULmoji spec
            url = f"https://wttr.in/{location}?format=%l:+%c+%t+%h+%w"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Example output: London: ⛅️ +8°C 71% ↙5km/h
            text = response.text.strip()
            
            # Simple parse
            parts = text.split(" ")
            return {
                "location": location,
                "display": text,
                "condition_emoji": parts[1] if len(parts) > 1 else "⚪",
                "temp": parts[2] if len(parts) > 2 else "unknown"
            }
        except Exception as e:
            return {
                "location": location,
                "display": f"{location}: Data Unavailable",
                "condition_emoji": "⚪",
                "temp": "N/A"
            }

    @staticmethod
    def get_risk_color(condition_emoji: str) -> str:
        # Mapping as per spec
        if condition_emoji in ["⛈️", "🌧️", "❄️"]:
            return "🔴"
        if condition_emoji in ["☁️", "⛅️"]:
            return "🟡"
        if condition_emoji in ["🌤️", "☀️"]:
            return "🟢"
        return "🔵"
