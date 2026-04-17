#!/bin/bash
# -*- coding: utf-8 -*-

# HELEN WULmoji + Weather Integration
# Fetches current weather and displays with WULmoji context
# Services: wttr.in (primary) + Open-Meteo (fallback)
# No API key required

set -euo pipefail

location="${1:-San Francisco}"
format="${2:-compact}"  # compact or full

# Colors for WULmoji (mapped to weather condition)
get_wulmoji_color() {
    local condition="$1"

    case "$condition" in
        # Storm conditions
        "⛈️"|"🌧️"|"🌩️"|"❄️"|"🌨️")
            echo "🔴"  # Critical/dangerous
            ;;
        # Cloudy/mixed
        "☁️"|"⛅️"|"🌦️"|"🌥️")
            echo "🟡"  # Caution
            ;;
        # Clear
        "🌤️"|"☀️"|"🌞")
            echo "🟢"  # Safe/normal
            ;;
        # Default
        *)
            echo "🔵"  # Informational
            ;;
    esac
}

# Fetch weather from wttr.in
fetch_weather_text() {
    local loc="$1"
    # Replace spaces with +
    loc="${loc// /+}"

    if command -v curl &> /dev/null; then
        curl -s "wttr.in/${loc}?format=%l:+%c+%t+%h+%w" 2>/dev/null || echo "weather unavailable"
    else
        echo "weather unavailable"
    fi
}

# Fetch weather from Open-Meteo (JSON, requires coordinates)
fetch_weather_json() {
    local lat="${1:-37.7749}"
    local lon="${2:--122.4194}"

    if command -v curl &> /dev/null; then
        curl -s "https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true" 2>/dev/null || echo "{}"
    else
        echo "{}"
    fi
}

# Get weather and determine color
get_weather_context() {
    local location="$1"

    # Try wttr.in first
    local weather_text
    weather_text=$(fetch_weather_text "$location")

    if [ "$weather_text" != "weather unavailable" ]; then
        # Extract condition emoji (second field)
        local condition=$(echo "$weather_text" | awk '{print $2}')
        local color=$(get_wulmoji_color "$condition")

        echo "$color|$weather_text"
    else
        # Fallback: no color, no weather
        echo "🔵|weather data unavailable"
    fi
}

# Main output
main() {
    local context
    context=$(get_weather_context "$location")

    local color="${context%%|*}"
    local weather="${context#*|}"

    # Output WULmoji header
    cat << EOF
IN WULmoji | ✝️🌹🌀 | 📜 | $color

[WEATHER_CONTEXT]
📍 $weather

EOF
}

# Run
main "$@"
