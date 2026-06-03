import requests
import random

with open("./keys.txt", "r") as keys:
    key = keys.read().splitlines()


class Weather:
    def __init__(self, location):
        self.location = location
        self.key = random.choice(key).strip()
    def check(self):
        self.url = f"http://api.openweathermap.org/data/2.5/weather?q={self.location}&appid={self.key}"
        self.response = requests.get(self.url)
        self.data = self.response.json()
    def retrieve(self):
        if self.data['cod'] != 404:
            return self.data
        else:
            return "Error 404"

weather = Weather("San Antonio")
weather.check()
print(weather.retrieve())