# Skyline - Weather made simple.

Skyline is a desktop weather application with a polished, animated interface for checking current conditions, short-term forecasts, weather insights, and saved locations.

![Skyline preview](preview.png)

## Features

- Current temperature, conditions, feels-like temperature, humidity, dew point, UV index, air quality, sunrise, and sunset.
- Hourly and multi-day forecasts with precipitation and wind information.
- Animated rain and snow effects that match the current weather.
- Search for locations and switch between them without restarting the app.
- A dashboard for saving and reordering up to five locations.
- Light and dark themes, plus metric/imperial unit preferences.
- Interactive weather map with precipitation, cloud, temperature, and wind layers.

## Requirements

- Python 3.10 or newer
- Windows 10 or 11 (the app uses Windows-specific window and system APIs)
- An active internet connection for weather, location, map, and insight data

## Installation

1. Open the repository's **Releases** page.

2. Download `installer.exe` from the latest release.

3. Open the downloaded installer and follow the on-screen instructions.

4. Launch Skyline from the Start menu or desktop shortcut after installation.

> `installer.exe` will be available once the first release is published.

## Running Skyline

Open Skyline from the Start menu or desktop shortcut. On first launch, Skyline attempts to detect your approximate location. If location detection is unavailable, use the search control to select a city manually.

## Usage

### Check another location

Use the search button in the app, enter a city or region, then select a result. Skyline reloads the weather data and map for that location.

### Manage saved locations

Open the dashboard to add locations, remove them, or drag cards to reorder them. Saved cards are stored in `dashboard.json`.

### Change units or theme

Open Settings to switch between Celsius/Fahrenheit, metric/imperial wind and precipitation units, and light/dark themes. Preferences are stored in `settings.json`.

### Use the weather map

Scroll to the weather map and use its control menu to switch between precipitation, clouds, temperature, and wind layers.

## Project files

- `main.py` — application window, views, controls, and interactions.
- `retrieve.py` — weather, forecast, dashboard, and insight data requests.
- `ui_engine.py` — reusable widgets, cards, map preview rendering, and visual effects.
- `settings.json` — local unit and theme preferences.
- `dashboard.json` — saved dashboard locations.

## Troubleshooting

- Map tiles and weather data require an internet connection.
- If location detection is unavailable, search for and select a city manually.
