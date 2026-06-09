from datetime import datetime, timezone, timedelta
import requests
import random


with open("./keys.txt", "r") as keys:
    key = keys.read().splitlines()


class Weather:
    def __init__(self, location):
        self.location = location
        self.key = random.choice(key).strip()
    def init_url(self, weather_type="condition"):
        latitude = str(self.location[0])
        longitude = str(self.location[1])
        if weather_type == "condition":
            self.url = f"http://api.openweathermap.org/data/2.5/weather?q={self.location}&appid={self.key}"
        elif weather_type == "hourly":
            self.url = f"https://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&units=imperial&appid={self.key}"
    def retrieve_current_condition(self):
        self.response = requests.get(self.url)
        self.data = self.response.json()
        if self.data['cod'] != 404:
            return self.data
        else:
            return "Error 404"
    def retrieve_hourly_forecast(self):
        self.response = requests.get(self.url)
        self.data = self.response.json()
        if self.data['cod'] != 404:
            return self.data
        else:
            return "Error 404"
    
    
weather = Weather((40.71, -74.01))
weather.init_url("hourly")
data = weather.retrieve_hourly_forecast()      
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
print(parse_hourly_forecast(data))