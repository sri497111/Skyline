import json

file = "./settings.json"

def load_settings():
    try:
        with open(file, "r") as settings:
            return json.load(settings)
    except FileNotFoundError:
        return {
            "units": {'speed': 'KPH', 'temperature': 'F', 'length': 'IN'},
            "theme": "dark"
        }

def update_settings(category, key, value):
    data = load_settings()

    if category in data and key in data[category]:
        data[category][key] = value

    with open(file, "w") as settings:
        json.dump(data, settings, indent=4)

def check_theme():
    with open(file, "r") as settings:
        data = json.load(settings)
        theme = data.get("theme", {})
        main = theme.get("main") if isinstance(theme, dict) else theme

        return 0 if main == "dark" else 1