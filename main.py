# Qt Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontDatabase, QPixmap
from PyQt5 import QtWidgets
from PyQt5.QtSvg import QSvgWidget

# Modules
from location import *
from retrieve import Weather, parse_hourly_forecast, parse_daily_forecast, get_uv
from ui_engine import Card, text, Button, poppins, svg

# System
from system import *
import sys
import datetime

# --------------------------------------------------------------------------


SIZE = (878, 550)

SPEED_UNIT = "MPH"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(SIZE[0], SIZE[1])
        # ---------------------- Window ---------------------- #
        self.windowsize = (SIZE[0], SIZE[1])
        self.refresh_rate = get_refresh_rate()
        self.frequency = int(round(1000/self.refresh_rate, 0))
        
        # ---------------------- Window ---------------------- #
        self.friction = 0.92
        self.sensitvity = 0.03
        self.yv = 0
        self.v = 0
        
        self.setStyleSheet("""
            QMainWindow {
                border-image: url('./Backgrounds/clear/blurred.png') 0 0 0 0 stretch stretch;
            }
        """)
        
        self.element = QPixmap("./Backgrounds/clear/element.png")
        
        # ---------------------- UI ---------------------- #
        
        # Init Weather
        self.location = (37.334606, -122.009102)
        self.weather_vars(self.location)
        
        
        # Init Viewport and screening (content)
        widget = QWidget()
        self.viewport = QWidget(widget)
        self.viewport.setGeometry(0, 0, 878, 1300)
        
        # Init Widgets
        self.status_bar()
        self.hourly()
        self.daily()
        self.uv_and_feels_like()
        
        
        
        
        main_layout = QVBoxLayout(self.viewport)
        main_layout.setContentsMargins(25, 75, 25, 25)
        main_layout.setSpacing(30)
        
        main_layout.addWidget(self.status)
        
        main_layout.addWidget(self.hourly_forecast)
        
        main_layout.addWidget(self.daily_forecast)
        
        main_layout.addWidget(self.uvf)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.intertia)
        self.timer.start(self.frequency)
        
        
        self.viewport.setLayout(main_layout)
        
        self.setCentralWidget(widget)
        
    def wheelEvent(self, event):
        self.v += event.angleDelta().y() * self.sensitvity
    def intertia(self):
        if self.v > 0.05 or self.v < -0.05:
            self.yv += self.v
            self.v *= self.friction
            
            self.viewport.move(0, int(self.yv))
            
            self.viewport.update()
            self.hourly_forecast.updatePixmap()
            self.daily_forecast.updatePixmap()
            self.uvf.updatePixmap()
            
            
        else:
            if self.v != 0:
                self.v = 0
                
    def daily(self):
        self.daily_forecast = Card(self.viewport, self.element, 500)
        self.daily_forecast.setContentsMargins(35,0,0,0)
        self.daily_layout = QVBoxLayout(self.daily_forecast)
        self.populate_daily_forecast(self.weather_daily_forecast_data)
    def populate_daily_forecast(self, forecast_data):
        # Scale Values
        num_pad = 5

        self.daily_layout.setAlignment(Qt.AlignLeft)
        self.daily_layout.setSpacing(0)
        
        data = self.weather_daily_forecast_data
        print(data)
        
        for i in range(5):
            horizontal_widget = QWidget()
            horizontal_widget.setFixedHeight(90)
            
            hbox = QHBoxLayout(horizontal_widget)
            hbox.setContentsMargins(20,0,0,0)
            hbox.setSpacing(25)
            
            cond = data[i][1]
            if cond.lower() == "clear":
                cond = svg("./Icons/clear-day.svg", 64, 64)
                
            elif cond.lower() == "clouds":
                cond = svg("./Icons/cloudy.svg", 64, 64)
            elif cond.lower() == "rain":
                cond = svg("./Icons/rain.svg", 64, 64)
            else:
                print(cond + " error dont have this one!")
            
            cond.setStyleSheet("padding-bottom: 8px;")
            hbox.addWidget(cond)
            
            day = data[i][0]
            day = text(day, "white", poppins("semi bold"), 20, horizontal_widget)
            day.setFixedWidth(140)
            
            min_max = data[i][2], data[i][3]
            min_max_string = f"{min_max[0]}\u00b0 / {min_max[1]}\u00b0"
            min_max = text(min_max_string, "white", poppins("semi bold"), 20, horizontal_widget)
            min_max.setFixedWidth(120)
            
            if int(data[i][4]) == 0:
                end_icon = svg("./Icons/wind.svg", 51, 51)
                num = text(str(data[i][5])+" "+SPEED_UNIT, "white", poppins("semi bold"), 17, horizontal_widget)
                num.setFixedWidth(85)
            else:
                end_icon = svg("./Icons/raindrop.svg", 64, 64)
                num = text(str(data[i][4])+" %", "white", poppins("semi bold"), 17, horizontal_widget)
                num.setFixedWidth(85)
                num.setStyleSheet(f"padding-top: {num_pad}px; color: white;")
                
            hbox.addWidget(day)
            hbox.addSpacing(80)
            hbox.addWidget(min_max)
            hbox.addSpacing(55)
            hbox.addWidget(end_icon)
            hbox.addWidget(num)
            self.daily_layout.addWidget(horizontal_widget)

    def hourly(self):
        self.hourly_forecast = Card(self.viewport, self.element, 200)
        self.timeline = QHBoxLayout(self.hourly_forecast)
        self.populate_hourly_forecast(self.weather_hourly_forecast_data)
        
    def populate_hourly_forecast(self, forecast_data):
        self.timeline.setAlignment(Qt.AlignCenter)
        self.timeline.setSpacing(60)
        for i in range(5):
            
            vertical_widget = QWidget()
            vdata = QVBoxLayout(vertical_widget)
            vdata.setContentsMargins(0,0,0,0)
            vdata.setSpacing(0)
            
            time = text(str(forecast_data[i][0]), "white", poppins("semi bold"), 18, vertical_widget)
            print(forecast_data[i])
            time.setAlignment(Qt.AlignCenter)
            
            
            if str(forecast_data[i][1]).lower() == "clouds":
                condition = svg("./Icons/cloudy.svg", 83, 83)
            elif str(forecast_data[i][1]).lower() == "clear":
                condition = svg("./Icons/clear-day.svg", 83, 83)
            elif str(forecast_data[i][1]).lower() == "rain":
                condition = svg("./Icons/rain.svg", 83, 83)
            else:
                condition = svg("./Icons/rain.svg", 64, 64)
            
            temp = text(" "+str(forecast_data[i][2])+"\u00b0", "white", poppins("semi bold"), 18, vertical_widget)
            temp.setAlignment(Qt.AlignCenter)
            
            
            vdata.addWidget(time)
            
            vdata.addWidget(condition)
            vdata.addSpacing(8)
            vdata.addWidget(temp)
            vdata.setAlignment(Qt.AlignCenter)
            
            self.timeline.addWidget(vertical_widget)
    
    def uv_and_feels_like(self):
        self.uvf = Card(self.viewport, self.element, 250)
        self.uvf.setContentsMargins(105,0,55,0)
        self.uvf_layout = QVBoxLayout(self.uvf)
        self.populate_uvf(self.uv_index, self.feels_like)
    
    def populate_uvf(self, uv, feel):
        vertical_widget = QWidget()
        hdata = QHBoxLayout(vertical_widget)
        hdata.setSpacing(25)
        hdata.addSpacing(50)
        hdata.addWidget(text("UV Index: "+str(self.uv_index), "white", poppins("semi bold"),30, vertical_widget))
        hdata.addSpacing(50)
        hdata.addWidget(text("Feels Like: ", "white", poppins("semi bold"),30, vertical_widget))
        self.uvf_layout.addWidget(vertical_widget)
        
        
        
    def weather_vars(self, location):
        self.current_weather = Weather(location)
        self.current_weather_data = self.current_weather.retrieve_current_weather()
        
        self.current_location_name = str(self.current_weather_data["name"])
        print(self.current_location_name)
        
        self.current_temp = str(round(int(self.current_weather_data['main']['temp']), 0))+"\u00b0"
        self.current_condition = str(self.current_weather_data["weather"][0]["main"])
        
        self.weather_forecast_data = self.current_weather.retrieve_forecast()
        self.weather_hourly_forecast_data = parse_hourly_forecast(self.weather_forecast_data, increment=5)
        
        self.weather_daily_forecast_data = parse_daily_forecast(self.weather_forecast_data)
        
        self.uv_index = get_uv(location)
        self.feels_like = self.current_weather_data['main']['feels_like']
        
    def status_bar(self):
        self.status = QWidget(self.viewport)
        self.status.setGeometry(35, 75, 828, 120)
        status_layout = QHBoxLayout(self.status)
        status_layout.setContentsMargins(20, 0, 35, 0)
        status_layout.setSpacing(15)
        
        if str(self.current_condition).lower() == "clouds":
                condition = svg("./Icons/cloudy.svg", 171, 171)
        elif str(self.current_condition).lower() == "clear":
            condition = svg("./Icons/clear-day.svg", 171, 171)
        elif str(self.current_condition).lower() == "rain":
            condition = svg("./Icons/rain.svg", 171, 171)
        
        temp = text(self.current_temp, "white", poppins("semi bold"), 60, self.status)
        temp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        temp.setContentsMargins(0, 12, 0, 0)
        temp.setMinimumWidth(200)
        
        status_layout.addWidget(condition)
        status_layout.addWidget(temp)
        
        status_layout.addStretch(1)
        
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_layout.setSpacing(5)
        
        condition = text(self.current_condition, "white", poppins("semi bold"), 45, self.status)
        condition.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        condition.setMaximumHeight(70)
        
        location = text(str(self.current_location_name), "white", poppins("semi bold"), 20, self.status)
        location.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        location.setMaximumHeight(30)
        location.setStyleSheet(location.styleSheet() + "; margin-right: 1px;")
        
        info_layout.addWidget(location)
        info_layout.addWidget(condition)
        
        status_layout.addLayout(info_layout)
        
def main():   
    app = QApplication(sys.argv)
    
    window = MainWindow()
    
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
