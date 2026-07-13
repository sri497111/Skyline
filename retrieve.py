from PyQt5.QtCore import QThread, pyqtSignal
from datetime import datetime, timezone, timedelta
from pathlib import Path
from ui_engine import get_map_preview
import requests
import random
import json

file = "./settings.json"

def check_theme():
    with open(file, "r") as settings:
        data = json.load(settings)
        theme = data.get("theme", {})
        main = theme.get("main") if isinstance(theme, dict) else theme

        return 0 if main == "dark" else 1

class Weather:
    def __init__(self, location):
        self.location = location
        self.lat= str(self.location[0])
        self.lon = str(self.location[1])

        print(f"Coords being sent to Vercel - ({self.lat}, {self.lon})")

        self.url = f"https://skyline-backend-xcrg.vercel.app/api/weather?lat={self.lat}&lon={self.lon}"
        self.response = requests.get(self.url)
        

        try:
            self.data = self.response.json()
        except:
            status = self.response.status_code
            snippet = self.response.text[:200].replace('\n', ' ')
            raise Exception(f"Vercel Error! Status code {status}\n Response snip - {snippet}")
        
    def retrieve_current_weather(self):
        return self.data['current']
    def retrieve_forecast(self):
        return self.data['forecast']
    def retrieve_uv(self):
        return self.data['uv']['now']['uv_index']


class WeatherWait(QThread):
    data = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, location):
        super().__init__()
        self.location = location
    def run(self):
        try:
            weather = Weather(self.location)
            
            theme = check_theme()

            if theme == 0: map_val = get_map_preview(305, theme="dark")
            else: map_val = get_map_preview(305, theme="light")


            weather_data = {
                "current": weather.retrieve_current_weather(),
                "forecast": weather.retrieve_forecast(),
                "uv": weather.retrieve_uv(),
                "map": map_val
            }
            self.data.emit(weather_data)
            
        except Exception as e:
            self.error.emit(str(e))


def parse_hourly_forecast(data, increment=8):
    forecast = []
    
    timezone_offset = data["city"]["timezone"]
    area_timezone = timezone(timedelta(seconds=timezone_offset))
    
    for i in range(increment):
        next3 = data['list'][i]
        
        time = next3["dt"]
        local_time = datetime.fromtimestamp(time, tz=area_timezone)
        
        time = f"{int(local_time.strftime('%I'))} {local_time.strftime('%p')}"
        
        conditions = next3["weather"][0]["main"]
        
        temp = round(next3["main"]["temp"])
        
        forecast.append([time, conditions, temp])

    return forecast

def parse_daily_forecast(data):
    day_list = []
    
    forecast = []
    
    for item in data["list"]:
        day = datetime.strptime(item["dt_txt"], "%Y-%m-%d %H:%M:%S").strftime("%A").lower()
        temp = item['main']['temp']
        condition = item['weather'][0]['main']
        wind_speed = item['wind']['speed']
        precip = (item.get('pop', 0) * 100)
        
        
        index = -1  
        for i in range(len(day_list)):
            if day_list[i][0] == day:
                index = i
                break
        if index == -1:
            day_list.append([day, [condition], [temp], [precip], [wind_speed]])
        else:
            day_list[index][1].append(condition)
            day_list[index][2].append(temp)
            day_list[index][3].append(precip)
            day_list[index][4].append(wind_speed)
    
    for day in day_list:
        day_of_week = str(day[0]).title()
        temps = day[2]
        conditions = day[1]
        precip = day[3]
        wind_speed = day[4]
        
        min_temp = round(min(temps))
        max_temp = round(max(temps))
        
        avg_precip = round(sum(precip)/len(precip))
        avg_wind = round(sum(wind_speed)/len(wind_speed))
        
        condition = max(set(conditions), key=conditions.count)
        
        forecast.append([day_of_week, condition, min_temp, max_temp, avg_precip, avg_wind])
        
    return forecast

def parse_forecast_for_precip(data):
    total = 0
    
    for item in data["list"][:8]:
        total += item.get("rain", {}).get("3h", 0)
    
    total_inches = total / 25.4
    
    return total_inches, round(total, 1)



def open_replace(path):
    file = Path(str(path))
    content = file.read_text()
    new_content = content.replace("REPLACE_KEY", "7dd61afc5903f81a45839eb528dcbabd")
    file.write_text(new_content)

def edit_html():
    open_replace("./map-light.html")
    open_replace("./map-dark.html")
    open_replace("./map-light-preview.html")
    open_replace("./map-dark-preview.html")