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
from retrieve import Weather, parse_hourly_forecast
from ui_engine import Card, text, Button, poppins, svg

# System
from system import *
import sys
import datetime

# --------------------------------------------------------------------------


SIZE = (878, 550)


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
        self.weather_vars((33.448376, -112.074036))
        
        # Init Viewport and screening (content)
        widget = QWidget()
        self.viewport = QWidget(widget)
        self.viewport.setGeometry(0, 0, 878, 1050)
        
        # Init Widgets
        self.status_bar()
        self.hourly()
        self.daily()
        
        
        main_layout = QVBoxLayout(self.viewport)
        main_layout.setContentsMargins(25, 75, 25, 25)
        main_layout.setSpacing(30)
        
        main_layout.addWidget(self.status)
        
        main_layout.addWidget(self.hourly_forecast)
        
        main_layout.addWidget(self.daily_forecast)
        
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
            self.hourly_forecast.updatePixmap()
            self.daily_forecast.updatePixmap()
            
        else:
            if self.v != 0:
                self.v = 0
        
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
            
            
            temp = text(" "+str(forecast_data[i][2])+"\u00b0", "white", poppins("semi bold"), 18, vertical_widget)
            temp.setAlignment(Qt.AlignCenter)
            
            
            vdata.addWidget(time)
            
            vdata.addWidget(condition)
            vdata.addSpacing(8)
            vdata.addWidget(temp)
            vdata.setAlignment(Qt.AlignCenter)
            
            self.timeline.addWidget(vertical_widget)
        
    def weather_vars(self, location):
        self.current_weather = Weather(location)
        self.current_weather.init_url()
        self.current_weather_data = self.current_weather.retrieve_current_weather()
        
        self.current_location_name = str(self.current_weather_data["name"])
        print(self.current_location_name)
        
        self.current_temp = str(round(int(self.current_weather_data['main']['temp']), 0))+"\u00b0"
        self.current_condition = str(self.current_weather_data["weather"][0]["main"])
        
        self.current_weather.init_url("hourly")
        self.weather_forecast_data = self.current_weather.retrieve_hourly_forecast()
        self.weather_forecast_data = parse_hourly_forecast(self.weather_forecast_data, increment=5)

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
        location.setStyleSheet(location.styleSheet() + "; margin-right: 2px;")
        
        info_layout.addWidget(location)
        info_layout.addWidget(condition)
        
        status_layout.addLayout(info_layout)
        
    def hourly(self):
        self.hourly_forecast = Card(self.viewport, self.element, 200)
        self.timeline = QHBoxLayout(self.hourly_forecast)
        self.populate_hourly_forecast(self.weather_forecast_data)
    
    def daily(self):
        self.daily_forecast = Card(self.viewport, self.element, 500)
        self.daily_forecast.setContentsMargins(35,0,0,0)

def main():   
    app = QApplication(sys.argv)
    
    window = MainWindow()
    
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
