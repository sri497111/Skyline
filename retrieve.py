from PyQt5.QtCore import QThread, pyqtSignal, QObject
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
    
class DashboardWeather:
    def __init__(self, loc1=[], loc2=[], loc3=[], loc4=[], loc5=[]):
        self.loc1 = loc1
        self.loc2 = loc2
        self.loc3 = loc3
        self.loc4 = loc4
        self.loc5 = loc5
        
        self.url = f"https://skyline-dashboard-backend.vercel.app/?lat1={self.loc1[0]}&lon1={self.loc1[1]}&lat2={self.loc2[0]}&lon2={self.loc2[1]}&lat3={self.loc3[0]}&lon3={self.loc3[1]}&lat4={self.loc4[0]}&lon4={self.loc4[1]}&lat5={self.loc5[0]}&lon5={self.loc5[1]}"
        print(self.url)
        self.response = requests.get(self.url)
        
        try:
            self.data = self.response.json()
        except:
            status = self.response.status_code
            snippet = self.response.text[:200].replace('\n', ' ')
            raise Exception(f"Vercel Error! Status code {status}\n Response snip - {snippet}")
        
    def retrieve_dashboard_weather(self):
        return self.data
    
class DashboardWeatherWait(QThread):
    data = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, loc1=[], loc2=[], loc3=[], loc4=[], loc5=[]):
        super().__init__()
        self.loc1 = loc1
        self.loc2 = loc2
        self.loc3 = loc3
        self.loc4 = loc4
        self.loc5 = loc5
    def run(self):
        try:
            weather = DashboardWeather(self.loc1, self.loc2, self.loc3, self.loc4, self.loc5)
            
            weather_data = weather.retrieve_dashboard_weather()
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

class Insights:
    def __init__(self, time, temp, feels, wind, uv, tmrw, forecast, additional=None):
        self.time = time
        self.temp = temp
        self.feels = feels
        self.wind = wind
        self.uv = uv
        self.tmrw = tmrw
        self.forecast = forecast
        self.additional = additional
    
    def retrieve_insights(self):
        self.url = f"https://skyline-insights-backend.vercel.app/api/weather"

        self.payload = {
            "time": self.time,
            "temp": self.temp,
            "feels": self.feels,
            "wind": self.wind,
            "uv": self.uv,
            "tmrw": self.tmrw,
            "forecast": self.forecast,
            "additional": "Null"
            
        }
        print(self.payload)

        if self.additional is not None:
            self.payload["additional"] = self.additional

        try:
            response = requests.post(self.url, json=self.payload)
            data = response.json()
            return data
        except Exception as e:
            print(e)

class WeatherWait(QThread):
    data = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, location, precise=True):
        super().__init__()
        self.location = location
        self.precise = precise

    def run(self):
        try:
            weather = Weather(self.location)
            
            theme = check_theme()

            if theme == 0: map_val = get_map_preview(self.location[0], self.location[1], theme="dark", precise=self.precise)
            else: map_val = get_map_preview(self.location[0], self.location[1], theme="light", precise=self.precise)

            weather_data = {
                "current": weather.retrieve_current_weather(),
                "forecast": weather.retrieve_forecast(),
                "uv": weather.retrieve_uv(),
                "map": map_val
            }

            dt = weather_data["current"]["dt"]
            timezones = weather_data["current"]["timezone"]
            timestamp = (dt) + (timezones)

            local_data = datetime.fromtimestamp(timestamp, tz=timezone.utc)

            formatted_time = local_data.strftime("%I:%M %p").lower()

            time = formatted_time

            temp = weather_data["current"]["main"]["temp"]
            feels = weather_data["current"]["main"]["feels_like"]
            wind = weather_data["current"]["wind"]["speed"]
            uv = weather_data["uv"]
            forecast_hourly = []
            forecast_data = weather_data["forecast"]
            daily = parse_daily_forecast(forecast_data)
            wind = str(daily[0][5])+"MPH"
            tmrw = f"cond: {str(daily[1][1])} min: {daily[1][2]} max: {daily[1][3]}"
            parsed_forecast = parse_hourly_forecast(forecast_data)
            for i in range(5):
                forecast_hourly.append([parsed_forecast[i][0], parsed_forecast[i][1], parsed_forecast[i][2]])
            
            insights = Insights(time, temp, feels, wind, uv, tmrw, forecast_hourly, additional=f"POP/Percent of Precipitation is {daily[0][4]}%")
            insights_data = insights.retrieve_insights()

            weather_data["insights"] = insights_data
            
            self.data.emit(weather_data)
            
        except Exception as e:
            self.error.emit(str(e))

def parse_forecast_for_precip(data):
    total = 0
    
    for item in data["list"][:8]:
        total += item.get("rain", {}).get("3h", 0)
    
    total_inches = total / 25.4
    
    return total_inches, round(total, 1)

def k():
    k="f@-~ 9f79@-~0ac-#@-~99d*5ac11 d1^(d0)b6b2@-~c9f6#$fe#@$*e1"
    k = k.strip().replace("@-~", "").replace("#$","").replace(" ", "").replace("-#", "").replace("(", "").replace(")", "").replace("^", "").replace("*", "").replace("$", "").replace("#", "").replace("@", "")
    return k

def open_replace(path):
    file = Path(str(path))
    content = file.read_text()
    new_content = content.replace("HASHEDRJK", f"{k()}")
    file.write_text(new_content)

def open_replace_reverse(path):
    file = Path(str(path))
    content = file.read_text()
    new_content = content.replace(f"{k()}", "HASHEDRJK")
    file.write_text(new_content)

def edit_html(reverse=False):
    if reverse:
        open_replace_reverse("./map-light.html")
        open_replace_reverse("./map-dark.html")
    else:
        open_replace("./map-light.html")
        open_replace("./map-dark.html")

class MapWorker(QObject):
    finished = pyqtSignal(object)
    def __init__(self, location, theme, precise):
        super().__init__()
        self.lat = location[0]
        self.lon = location[1]
        self.theme = theme
        self.precise = precise

    def run(self):
        map_pix = get_map_preview(self.lat, self.lon, theme=self.theme, precise=self.precise)
        self.finished.emit(map_pix)