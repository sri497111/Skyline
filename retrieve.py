from datetime import datetime, timezone, timedelta
import requests
import random


with open("./keys.txt", "r") as keys:
    key = keys.read().splitlines()


class Weather:
    def __init__(self, location):
        self.location = location
        self.key = random.choice(key).strip()
        self.lat= str(self.location[0])
        self.lon = str(self.location[1])
        
    def retrieve_current_weather(self):
        self.url = f"http://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&units=imperial&appid={self.key}"
        self.response = requests.get(self.url)
        self.data = self.response.json()
        if self.data['cod'] != 404:
            return self.data
        else:
            return "Error 404"
    def retrieve_forecast(self):
        self.url = f"https://api.openweathermap.org/data/2.5/forecast?lat={self.lat}&lon={self.lon}&units=imperial&appid={self.key}"
        self.response = requests.get(self.url)
        self.data = self.response.json()
        if self.data['cod'] != 404:
            return self.data
        else:
            return "Error 404"

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

def get_uv(coords):
    url = f"https://uvindexapi.com/api/v1/forecast?latitude={coords[0]}&longitude={coords[1]}&timezone=Auto"
    response = requests.get(url)
    data = response.json()
    return int(data['now']['uv_index'])

