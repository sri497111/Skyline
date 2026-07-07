import json

file = "./settings.json"

def load_settings():
    try:
        with open(file, "r") as settings:
            return json.load(settings)
    except FileNotFoundError:
        return {
            "units": {'speed': 'KPH', 'temperature': 'F', 'length': 'IN'},
            "theme": {'map': 'light'}
        }

def update_settings(category, key, value):
    data = load_settings()

    if category in data and key in data[category]:
        data[category][key] = value

    with open(file, "w") as settings:
        json.dump(data, settings, indent=4)
