# Qt Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QSpacerItem, QSizePolicy, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QEasingCurve, QEventLoop, QEvent, QParallelAnimationGroup, QPoint, QThread, QRectF
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import QGraphicsBlurEffect, QGraphicsOpacityEffect, QFrame
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtGui import QPixmap, QPainterPath, QRegion, QFont, QPainter, QBrush, QIcon
from PyQt5 import sip

# Modules
from ui_engine import Card, text, Button, poppins, svg, hover_svg, Loading_Icon, Popup, RadioButton, mouse_press_dim, mouse_release_dim, hover_text, WeatherCard
from retrieve import Weather, WeatherWait, DashboardWeather, DashboardWeatherWait, MapWorker, Insights, parse_hourly_forecast, parse_daily_forecast, parse_forecast_for_precip, edit_html, get_map_preview
from settings import load_settings, update_settings, check_theme
from system import internet_check
from location import *

# System    
from system import *
import webbrowser
import subprocess
import platform
import datetime
import random
import sys
import requests
import os
import gc

# Parse
import json

# --------------------------------------------------------------------------

SIZE = (878, 550)

SPEED_UNIT = "MPH"
LENGTH_UNIT = "IN"

refresh = get_refresh_rate()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(SIZE[0], SIZE[1])
        # ---------------------- Window ---------------------- #
        self.windowsize = (SIZE[0], SIZE[1])
        self.refresh_rate = refresh
        self.frequency = int(round(1000/self.refresh_rate, 0))
        self.active_threads = []
        
        # ---------------------- Window ---------------------- #
        self.friction = 0.92
        self.sensitvity = 0.03
        self.yv = 0
        self.v = 0

        theme = check_theme()
        
        self.centralwidget = QWidget(self)
        self.centralwidget.setStyleSheet("background: #0b0d0f;")
        self.setCentralWidget(self.centralwidget)   

        self.bg = QLabel(self.centralwidget)
        self.bg.setScaledContents(True)
        self.bg.setGeometry(0,0,self.width(),self.height())
        self.bg.setPixmap(QPixmap("./Backgrounds/dark-theme.png"))

        self.bg_fade_effect = QGraphicsOpacityEffect(self.bg)
        self.bg_fade_effect.setOpacity(1.0)
        self.bg.setGraphicsEffect(self.bg_fade_effect)

        self.weather_bg_label = QLabel(self.centralwidget)
        self.weather_bg_label.setScaledContents(True)
        self.weather_bg_label.setGeometry(0,0,self.width(),self.height())

        self.weather_fade_effect = QGraphicsOpacityEffect(self.weather_bg_label)
        self.weather_fade_effect.setOpacity(0.0)
        self.weather_bg_label.setGraphicsEffect(self.weather_fade_effect)


        self.weather_bg_label.lower()
        self.bg.lower()

        
        self.element = QPixmap("./Backgrounds/clear/element.png")
        
        # ---------------------- UI ---------------------- #
        
        self.network = QNetworkAccessManager()

        self.first_load = True

        self.popup_active = False

        self.initial_place = True

        self.add_coords = None

        self.precise = True
        
        # Init Weather
        current_loc = current_location("coords")
        self.location = (current_loc[0], current_loc[1])

        self.dash_weather = []

        # Init Viewport and screening (content)

        self.viewport = QWidget(self.centralwidget)
        self.viewport.setGeometry(0, 0, 878, 2280)
        self.viewport.setStyleSheet("background: transparent; border: none; border-radius: 0px;")
        
        edit_html()

        self.ui_blur = QGraphicsBlurEffect()
        self.ui_blur.setBlurRadius(40)
        self.ui_blur.setBlurHints(QGraphicsBlurEffect.QualityHint)
        self.viewport.setGraphicsEffect(self.ui_blur)
        

        self.loading = Loading_Icon("./Icons/loading.svg", 64 )
        self.loading.setParent(self.centralwidget)
        self.loading.move((self.width()-self.loading.width())//2, (self.height()-self.loading.height())//2)
        self.loading.show()
        self.loading.raise_()

        self.wait = WeatherWait(self.location, precise=self.precise)
        self.wait.data.connect(self.loaded)
        self.wait.error.connect(self.error)

        self.wait.start()

        try:
            with open("./dashboard.json", "r") as d:
                dash_config = json.load(d)
        except Exception as e:
            print(e)

        locs = []

        for i in range(1,6):
            card_info = dash_config.get(f"card{i}")
            if isinstance(card_info, dict) and "lat" in card_info and "lon" in card_info:
                locs.append([card_info.get("lat", 0), card_info.get("lon", 0)])
            else:
                locs.append([0, 0])
        
        self.dash_wait = DashboardWeatherWait(locs[0], locs[1], locs[2], locs[3], locs[4])
        self.dash_wait.data.connect(self.dash_data_loaded)
        self.dash_wait.start()


    def set_background_image(self, condition, desc):
        if self.current_weather_id == 800:
            if self.ismorning:
                self.bg_pixmap = QPixmap("./Backgrounds/clear/blurred.png")
                self.element = QPixmap("./Backgrounds/clear/element.png")
            else:
                self.bg_pixmap = QPixmap("./Backgrounds/clear/blurred1.png")
                self.element = QPixmap("./Backgrounds/clear/element1.png")
        
        elif self.current_weather_id == 804:
            self.current_condition = "Cloudy"
            if self.ismorning:
                choice = random.choice([1, 2])
                if choice == 1:
                    self.bg_pixmap = QPixmap("./Backgrounds/cloudy/blurred.png")
                    self.element = QPixmap("./Backgrounds/cloudy/element.png")
                else:
                    self.bg_pixmap = QPixmap("./Backgrounds/cloudy/blurred2.png")
                    self.element = QPixmap("./Backgrounds/cloudy/element2.png")
            else:
                self.bg_pixmap = QPixmap("./Backgrounds/cloudy/blurred1.png")
                self.element = QPixmap("./Backgrounds/cloudy/element1.png")

        elif self.current_weather_id == 801 or self.current_weather_id == 802:
            self.current_condition = "Partly Cloudy"
            if self.ismorning:
                self.bg_pixmap = QPixmap("./Backgrounds/partly/blurred1.png")
                self.element = QPixmap("./Backgrounds/partly/element1.png")
            else:
                self.bg_pixmap = QPixmap("./Backgrounds/partly/blurred2.png")
                self.element = QPixmap("./Backgrounds/partly/element2.png")
        elif self.current_weather_id == 803:
            self.current_condition = "Mostly Cloudy"
            if self.ismorning:
                self.bg_pixmap = QPixmap("./Backgrounds/partly/blurred1.png")
                self.element = QPixmap("./Backgrounds/partly/element1.png")
            else:
                self.bg_pixmap = QPixmap("./Backgrounds/partly/blurred2.png")
                self.element = QPixmap("./Backgrounds/partly/element2.png")

        elif self.current_weather_id in (500, 501, 502, 503, 504, 520, 521, 522, 531):
            if self.current_weather_id == 500:
                self.current_condition = "Light Rain"
            elif self.current_weather_id == 501:
                self.current_condition = "Rain"
            elif self.current_weather_id in (502, 503, 504):
                self.current_condition = "Heavy Rain"
            elif self.current_weather_id in (520, 521, 522, 531):
                self.current_condition = "Showers"
            else:
                self.current_condition = "Rain"

            if self.ismorning:
                self.bg_pixmap = QPixmap("./Backgrounds/cloudy/blurred.png")
                self.element = QPixmap("./Backgrounds/cloudy/element.png")
            else:
                self.bg_pixmap = QPixmap("./Backgrounds/cloudy/blurred1.png")
                self.element = QPixmap("./Backgrounds/cloudy/element1.png")
        
        elif self.current_weather_id in (200, 201, 202, 210, 211, 212, 221, 230, 231, 232):
            self.current_condition = "Thunderstorm"
            if self.ismorning:
                choice = random.choice([1, 2])
                if choice == 1:
                    self.bg_pixmap == QPixmap("./Backgrounds/thunderstorm/blurred.png")
                    self.element = QPixmap("./Backgrounds/thunderstorm/element.png")
                else:
                    self.bg_pixmap = QPixmap("./Backgrounds/thunderstorm/blurred1.png")
                    self.element = QPixmap("./Backgrounds/thunderstorm/element1.png")
            else:
                self.bg_pixmap = QPixmap("./Backgrounds/thunderstorm/blurred2.png")
                self.element = QPixmap("./Backgrounds/thunderstorm/element2.png")
        
        elif self.current_weather_id in (300, 301, 302, 310, 311, 312, 321):
            self.current_condition = "Drizzle"
            self.bg_pixmap = QPixmap("./Backgrounds/cloudy/blurred.png")
            self.element = QPixmap("./Backgrounds/cloudy/element.png")

        elif self.current_weather_id in (600, 601, 602, 611, 612, 615, 616, 620, 621, 621):
            self.current_condition = "Snow"
            if self.ismorning:
                self.bg_pixmap = QPixmap("./Backgrounds/snow/blurred.png")
                self.element = QPixmap("./Backgrounds/snow/element.png")
            else:
                self.bg_pixmap = QPixmap("./Backgrounds/snow/blurred1.png")
                self.element = QPixmap("./Backgrounds/snow/element1.png")

        elif self.current_weather_id == 611:
            self.current_condition = "Hail"
            if self.ismorning:
                self.bg_pixmap = QPixmap("./Backgrounds/hail/blurred.png")
                self.element = QPixmap("./Backgrounds/hail/element.png")
            else:
                self.bg_pixmap = QPixmap("./Backgrounds/hail/blurred1.png")
                self.element = QPixmap("./Backgrounds/hail/element1.png")
        
        elif self.current_weather_id == 721:
            self.current_condition = "Haze"
            if self.ismorning:
                self.bg_pixmap = QPixmap("./Backgrounds/fog/blurred.png")
                self.element = QPixmap("./Backgrounds/fog/element.png")
            else:
                self.bg_pixmap = QPixmap("./Backgrounds/fog/blurred1.png")
                self.element = QPixmap("./Backgrounds/fog/element1.png")

        elif self.current_weather_id == 731:
            self.current_condition = "Dust"
            if self.ismorning:
                self.bg_pixmap = QPixmap("./Backgrounds/dust/blurred.png")
                self.element = QPixmap("./Backgrounds/dust/element.png")
            else:
                self.bg_pixmap = QPixmap("./Backgrounds/dust/blurred1.png")
                self.element = QPixmap("./Backgrounds/dust/element1.png")

        elif self.current_weather_id in (701, 741):
            self.current_condition = "Fog"
            if self.ismorning:
                self.bg_pixmap = QPixmap("./Backgrounds/fog/blurred.png")
                self.element = QPixmap("./Backgrounds/fog/element.png")
            else:
                self.bg_pixmap = QPixmap("./Backgrounds/fog/blurred1.png")
                self.element = QPixmap("./Backgrounds/fog/element1.png")
        self.weather_bg_label.setPixmap(self.bg_pixmap)

        self.anim_weather_in = QPropertyAnimation(self.weather_fade_effect, b'opacity')
        self.anim_weather_in.setDuration(400)
        self.anim_weather_in.setStartValue(0.0)
        self.anim_weather_in.setEndValue(1.0)
        self.anim_weather_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim_weather_in.start()

        
    def loaded(self, data):    
        self.fade = QGraphicsOpacityEffect(self.viewport)
        self.fade.setOpacity(0.0)
        self.viewport.setGraphicsEffect(self.fade)

        self.current_weather = data['current']
        
        print(data['insights'])
        self.insights_data = data['insights']["insights"]

        self.insights_list = []
        if isinstance(self.insights_data, str) and self.insights_data.strip():
            split_insights = self.insights_data.split(";")
            for insight_text in split_insights:
                if "--" in insight_text:
                    self.insights_list.append(insight_text.split("--"))
                else:
                    self.insights_list.append(["Weather Insight", insight_text.strip()])

        if not self.insights_list:
            self.insights_list = [["Weather Insight", "No insights available."], ["Weather Insight", "No insights available."], ["Weather Insight", "No insights available."]]

        self.current_weather_data = self.current_weather

        if hasattr(self, 'target_location') and self.target_location:
            self.current_location_name = self.target_location
            self.target_location = None
        else:
            self.current_location_name = str(self.current_weather_data["name"])
        
        self.current_temp = str(round(int(self.current_weather_data['main']['temp']), 0))
        self.raw_temp = round(int(self.current_weather_data['main']['temp']), 0)

        self.current_condition = str(self.current_weather_data["weather"][0]["main"])
        self.current_weather_description = str(self.current_weather_data["weather"][0]["description"])
        self.current_weather_id = int(self.current_weather_data["weather"][0]["id"])
        
        self.weather_forecast_data = data['forecast']
        self.weather_hourly_forecast_data = parse_hourly_forecast(self.weather_forecast_data, increment=5)
        
        self.weather_daily_forecast_data = parse_daily_forecast(self.weather_forecast_data)
        
        self.feels_like = round(int(self.current_weather_data['main']['feels_like']))
        
        self.precip_inch = parse_forecast_for_precip(self.weather_forecast_data)[0]
        self.precip_cm = parse_forecast_for_precip(self.weather_forecast_data)[1]
        
        self.uv_index = data['uv']

        self.map_pixmap = data['map']

        self.aqi_index = data['aqi']

        self.loc = current_location("coords")
        self.lat = self.loc[0]
        self.lon = self.loc[1]
        humid = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={self.location[0]}&longitude={self.location[1]}&current=relative_humidity_2m,dew_point_2m").json()
        
        self.humidity = int(humid['current']['relative_humidity_2m'])

        self.raw_dew= int(humid['current']['dew_point_2m'])
        
        temp_unit = load_settings()
        is_fahrenheit = temp_unit['units']['temperature'] == "F"
        if is_fahrenheit:
            self.dew_point = round((self.raw_dew*9)/5+32)
        else:
            self.dew_point = int(self.raw_dew)

        sunrise_unix = self.current_weather_data['sys']['sunrise']
        sunset_unix = self.current_weather_data['sys']['sunset']

        current_time = datetime.datetime.now(datetime.timezone.utc).timestamp()
        if current_time < sunrise_unix or current_time > sunset_unix:
            self.ismorning = False
        else:
            self.ismorning = True
        
        tz_offset = self.current_weather_data['timezone']

        local_sunrise = datetime.datetime.fromtimestamp(sunrise_unix, datetime.timezone.utc) + datetime.timedelta(seconds=tz_offset)
        local_sunset = datetime.datetime.fromtimestamp(sunset_unix, datetime.timezone.utc) + datetime.timedelta(seconds=tz_offset)

        self.sunrise = local_sunrise.strftime("%#I:%M %p")
        self.sunset = local_sunset.strftime("%#I:%M %p")

        self.set_background_image(self.current_condition, self.current_weather_description)

        # Init Widgets

        self.menu_bar()
        self.status_bar()
        self.hourly()
        self.daily()
        self.insights()
        self.uv_and_feels_like()
        self.humidity_air_sun()
        self.weather_map()
        
        main_layout = QVBoxLayout(self.viewport)
        main_layout.setContentsMargins(25, 75, 25, 25)
        main_layout.setSpacing(0)
        
        main_layout.addWidget(self.menu)
        
        main_layout.addSpacing(0)

        main_layout.addWidget(self.status)
        
        main_layout.addSpacing(30)

        main_layout.addWidget(self.hourly_forecast)
        
        main_layout.addSpacing(30)

        main_layout.addWidget(self.daily_forecast)
        
        main_layout.addSpacing(30)

        main_layout.addWidget(self.insights_card)

        main_layout.addSpacing(30)

        main_layout.addWidget(self.uvf)

        main_layout.addSpacing(30)

        main_layout.addWidget(self.has)

        main_layout.addSpacing(30)
        
        main_layout.addWidget(self.weather_map_card)

        self.viewport.setLayout(main_layout)

        QApplication.processEvents()

        self.menu_card.updatePixmap()
        self.hourly_forecast.updatePixmap()
        self.daily_forecast.updatePixmap()
        self.insights_card.updatePixmap()
        self.uvf.updatePixmap()
        self.has.updatePixmap()
        self.weather_map_card.updatePixmap()

        theme_index = check_theme()
        self.apply_theme(theme_index)

        QApplication.processEvents()

        self.timer = QTimer()
        self.timer.timeout.connect(self.inertia)
        self.timer.start(self.frequency)

        self.load_fade = QGraphicsOpacityEffect(self.loading)
        self.load_fade.setOpacity(0.0)
        
        if not self.first_load:
            self.loading = Loading_Icon("./Icons/loading.svg", 64)
            self.loading.setParent(self.centralwidget)
            self.loading.move((self.width()-self.loading.width())//2, (self.height()-self.loading.height())//2)
            self.loading.show()
            self.loading.raise_()
            self.loading.setGraphicsEffect(self.load_fade)

        self.fade_out = QPropertyAnimation(self.load_fade, b"opacity")
        self.fade_out.setDuration(400)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)

        def cleanup():
            if hasattr(self, 'loading') and self.loading is not None:
                if hasattr(self.loading, "timer"):
                    self.loading.timer.stop()
                self.loading.hide()
                self.loading.deleteLater()
                self.loading = None

        self.fade_out.finished.connect(cleanup)

        self.fade_in = QPropertyAnimation(self.fade, b"opacity")
        self.fade_in.setDuration(400)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        
        self.fade_in.finished.connect(lambda: self.viewport.setGraphicsEffect(None))

        self.fade_out.finished.connect(self.fade_in.start)

        QTimer.singleShot(10, self.fade_out.start)
        


    def error(self, msg):
        print(f"Error -                {msg}")
        error_label = text("Error retrieving data...", "white", poppins("semi bold"), 20, self.viewport)
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setGeometry(0, 0, self.viewport.width(), self.viewport.height())
        error_label.show()

    def dash_data_loaded(self, data):
        self.dash_weather_data = data

        self.dash_weather = []

        if hasattr(self, 'dashboardpop') and self.dashboardpop is not None and not sip.isdeleted(self.dashboardpop):
            self.update_dashboard()
        
        for i in range(1,6):
            current_key = f"current{i}"

            if current_key not in self.dash_weather_data:
                continue

            hi_lo_key = f"hi_lo{i}"

            current_info = self.dash_weather_data.get(current_key, {})
            hi_lo_info = self.dash_weather_data.get(hi_lo_key, {})

            if current_info and hi_lo_info:
                location_name = current_info.get("name", f"Card {i}")
                
                weather_list = current_info.get("weather", [])
                condition = weather_list[0].get("id", "N/A") if weather_list else "N/A"

                desc = weather_list[0].get("description", "N/A") if weather_list else "N/A"
                
                main_data = current_info.get("main", {})
                current_temp = str(int(round(main_data.get("temp", 0))))

                daily_min_list = hi_lo_info.get("daily", {}).get('temperature_2m_min', [])
                daily_max_list = hi_lo_info.get("daily", {}).get('temperature_2m_max', [])

                hi = str(int(round(daily_max_list[0]))) if daily_max_list else "N/A"
                low = str(int(round(daily_min_list[0]))) if daily_min_list else "N/A"

                sys_data = current_info.get("sys", {})
                ismorning = sys_data.get("sunrise", 0) <= datetime.datetime.now(datetime.timezone.utc).timestamp() < sys_data.get("sunset", 0)

                self.dash_weather.append([location_name, condition, current_temp, hi, low, desc, ismorning])




    def wheelEvent(self, event):
        self.v += event.angleDelta().y() * self.sensitvity
    def inertia(self):
        if self.v > 0.05 or self.v < -0.05:
            self.yv += self.v
            self.v *= self.friction
            
            if hasattr(self, 'dashboardpop') and self.dashboardpop is not None and not sip.isdeleted(self.dashboardpop):
                if hasattr(self, 'dashboard_container') and not sip.isdeleted(self.dashboard_container):
                    
                    if self.yv > 0:
                        self.yv = 0
                        self.v = 0
                    elif self.yv < -620:
                        self.yv = -620
                        self.v = 0        
                    
                    self.sensitvity = 0.01
                    self.dashboard_container.move(self.dashboard_container.x(), int(self.yv))
                    
                    if hasattr(self, 'move_menu') and self.move_menu is not None and not sip.isdeleted(self.move_menu):
                        self.move_menu.move(self.move_menu.x(), self.move_menu_relative+int(self.yv))

                    for card in self.dash_cards:
                        if card and not sip.isdeleted(card):
                            card.updatePixmap()

            else:
                if self.yv > 0:
                    self.yv = 0
                    self.v = 0
                elif self.yv < -1820:
                    self.yv = -1820
                    self.v = 0
                
                self.sensitvity = 0.03
                self.viewport.move(0, int(self.yv))

                if hasattr(self, 'menu_card') and self.menu_card is not None and not sip.isdeleted(self.menu_card):
                    self.menu_card.updatePixmap()
                if hasattr(self, 'hourly_forecast') and self.hourly_forecast is not None and not sip.isdeleted(self.hourly_forecast):
                    self.hourly_forecast.updatePixmap()
                if hasattr(self, 'daily_forecast') and self.daily_forecast is not None and not sip.isdeleted(self.daily_forecast):
                    self.daily_forecast.updatePixmap()
                
                if hasattr(self, 'insights_card') and self.insights_card is not None and not sip.isdeleted(self.insights_card):
                    self.insights_card.updatePixmap()
                    if hasattr(self, 'insight_widget') and self.insight_widget is not None and not sip.isdeleted(self.insight_widget):
                        self.insight_widget.update()
                    if hasattr(self, 'insights_title_fade') and not sip.isdeleted(self.insights_title_fade):
                        self.insights_title_fade.update()
                    if hasattr(self, 'insights_title') and not sip.isdeleted(self.insights_title):
                        self.insights_title.repaint()
                        self.insights_title.raise_()
                    if hasattr(self, 'insights_body_fade') and not sip.isdeleted(self.insights_body_fade):
                        self.insights_body_fade.update()
                    if hasattr(self, 'insights_body') and not sip.isdeleted(self.insights_body):
                        self.insights_body.repaint()
                        self.insights_body.raise_()
                    if hasattr(self, 'dot1opacity') and not sip.isdeleted(self.dot1opacity):
                        self.dot1opacity.update()
                    if hasattr(self, 'dot1') and not sip.isdeleted(self.dot1):
                        self.dot1.repaint()
                        self.dot1.raise_()
                    if hasattr(self, 'dot2opacity') and not sip.isdeleted(self.dot2opacity):
                        self.dot2opacity.update()
                    if hasattr(self, 'dot2') and not sip.isdeleted(self.dot2):
                        self.dot2.repaint()
                        self.dot2.raise_()
                    if hasattr(self, 'dot3opacity') and not sip.isdeleted(self.dot3opacity):
                        self.dot3opacity.update()
                    if hasattr(self, 'dot3') and not sip.isdeleted(self.dot3):
                        self.dot3.repaint()
                        self.dot3.raise_()
                    
                
                if hasattr(self, 'uvf') and self.uvf is not None and not sip.isdeleted(self.uvf):
                    self.uvf.updatePixmap()
                if hasattr(self, 'has') and self.has is not None and not sip.isdeleted(self.has):
                    self.has.updatePixmap()
                if hasattr(self, 'weather_map_card') and self.weather_map_card is not None and not sip.isdeleted(self.weather_map_card):
                    self.weather_map_card.updatePixmap()
                
            
        else:
            if self.v != 0:
                self.v = 0
    def eventFilter(self, watched, event):
        if event.type() == QEvent.Wheel:
            self.v += event.angleDelta().y() * self.sensitvity
            return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if hasattr(self, "popup_card") and self.popup_card is not None:
            if not sip.isdeleted(self.popup_card):
                try:
                    pos = self.centralWidget().mapFrom(self, event.pos())
                    
                    if not self.popup_card.geometry().contains(pos):
                        self.hide_popup()
                except RuntimeError:
                    self.popup_card = None
            else:
                self.popup_card = None
                
        super().mousePressEvent(event)
        
    def menu_bar(self):
        self.menu = QWidget(self.viewport)
        self.menu_place = QHBoxLayout(self.menu)
        self.menu_place.setContentsMargins(0, 0, 20, 0)
        
        self.menu_card = Card(self.viewport, self.element, 60, radius=30, raise_dark=False)
        self.menu_card.setFixedWidth(225)
        self.menu_card.setContentsMargins(0, 0, 0, 0)

        self.menu_place.addWidget(self.menu_card, alignment=Qt.AlignRight)

        self.menu_layout = QHBoxLayout(self.menu_card)
        self.menu_layout.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.menu_layout.setContentsMargins(20,0,20,0)
        self.menu_layout.setSpacing(15)
        
        search = hover_svg("./Icons/search.svg", 30, 30)
        search.setCursor(Qt.PointingHandCursor)
        search.mousePressEvent = mouse_press_dim(search)
        search.mouseReleaseEvent = mouse_release_dim(search, self.search)
        self.menu_layout.addWidget(search)

        dashboard = hover_svg("./Icons/places.svg", 30, 30)
        dashboard.setCursor(Qt.PointingHandCursor)
        dashboard.mousePressEvent = mouse_press_dim(dashboard)
        dashboard.mouseReleaseEvent = mouse_release_dim(dashboard, self.dashboard)
        self.menu_layout.addWidget(dashboard)
        
        settings = hover_svg("./Icons/settings.svg", 30, 30)
        settings.setCursor(Qt.PointingHandCursor)
        settings.mousePressEvent = mouse_press_dim(settings)
        settings.mouseReleaseEvent = mouse_release_dim(settings, self.settings)
        self.menu_layout.addWidget(settings)

    
    def search(self, event, change=True):
        self.search_change_mode = change


        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.execute_search)

        if not hasattr(self, 'searchpop') or self.searchpop == None:
            
            theme = check_theme()
            
            self.searchpop = Popup(self)
            self.searchpop.destroyed.connect(lambda: setattr(self, 'searchpop', None))
            
            if theme == 0 and self.searchpop:
                self.searchpop.dim.setStyleSheet("background: rgba(0,0,0,0);")
            elif theme == 1 and self.searchpop:
                self.searchpop.dim.setStyleSheet("background: rgba(255,255,255,15);")


            self.search_bar = Card(self.searchpop, self.element, 70, radius=35, raise_dark=False) 
            self.search_bar.setFixedWidth(600)

            

            if theme == 0:
                self.search_bar.dark.setStyleSheet(f"""
                    background: rgba(0,0,0,50);
                    border-radius: {35}px;
                """)
                
            else:
                self.search_bar.dark.setStyleSheet(f"""
                    background: rgba(255,255,255,30);
                    border-radius: {35}px;
                """)

            search_layout = QHBoxLayout(self.search_bar)
            search_layout.setContentsMargins(40,0,40,0)

            self.location_search = QLineEdit(self.search_bar)
            self.location_search.setPlaceholderText("Search an adress, city or place.")
            self.location_search.setStyleSheet("background: transparent; border: none; color: white; font-size: 18px;")
            self.location_search.setFont(QFont(poppins("semi bold"), 12))
            self.location_search.textChanged.connect(lambda: self.search_timer.start(250))

            search_layout.addWidget(self.location_search, alignment=Qt.AlignVCenter)

            self.suggestions = Card(self.searchpop, self.element, 400, raise_dark=False, radius=45)

            self.suggestions.dark.setStyleSheet(f"""
                background: rgba(0,0,0,50);
                border-radius: {45}px;
            """)

            if theme == 0:
                self.suggestions.dark.setStyleSheet(f"""
                    background: rgba(0,0,0,50);
                    border-radius: {45}px;
                """)
            else:
                self.suggestions.dark.setStyleSheet(f"""
                    background: rgba(255,255,255,30);
                    border-radius: {35}px;
                """)

            self.search_bar.updatePixmap()
            self.suggestions.updatePixmap()

            self.suggestions_layout = QVBoxLayout(self.suggestions)
            self.suggestions_layout.setContentsMargins(50,35,50,35)
            self.suggestions_layout.setSpacing(5)
            

            self.searchpop.popup_layout.addWidget(self.search_bar, alignment=Qt.AlignCenter)
            self.searchpop.popup_layout.addWidget(self.suggestions)

            if change:
                self.execute_search()
            else:
                self.execute_search(change=False)

            QApplication.processEvents()

            self.search_bar.updatePixmap()
            self.suggestions.updatePixmap()

    def execute_search(self, change=None):
        if change is None:
            change = getattr(self, 'search_change_mode', True)
        

        search_query = self.location_search.text().strip()
        self.current_query = search_query

        change_type = "regular" if not change else "change"

        while self.suggestions_layout.count():
            child = self.suggestions_layout.takeAt(0)
            wid = child.widget()
            if wid is not None: 
                wid.deleteLater()
        

        if search_query == "":

            self.suggestions_layout.setAlignment(Qt.AlignCenter)
            begin_text = text("Begin Searching.", "white", poppins("semi bold"), 14, parent=self.suggestions, transparency=True)
            self.suggestions_layout.addWidget(begin_text, alignment=Qt.AlignCenter)
            begin_text.show()
            QApplication.processEvents()
            self.suggestions.updatePixmap()
            
            return

        begin_text = None
        self.suggestions_layout.setAlignment(Qt.AlignCenter)
        search_loading = Loading_Icon("./Icons/loading.svg", 48)
        self.suggestions_layout.addWidget(search_loading, alignment=Qt.AlignCenter)
        child.widget().hide() if child.widget() is not None else None
        QApplication.processEvents()
        self.suggestions.updatePixmap()

        suggestion_url = f"https://geocoding-api.open-meteo.com/v1/search?name={self.location_search.text()}&count=8&language=en&format=json"

        try: 
            reply = self.network.get(QNetworkRequest(QUrl(suggestion_url)))
            loop = QEventLoop()
            reply.finished.connect(loop.quit)
            loop.exec_()

        except:
            print("Data retrieval error")
            search_loading.deleteLater()
            return
        
        if self.current_query != search_query:
            if not sip.isdeleted(search_loading):
                search_loading.deleteLater()
            return

        if not sip.isdeleted(search_loading):
            search_loading.hide()
            search_loading.deleteLater()
        

        data = json.loads(str(reply.readAll(), 'utf-8'))
        places = data.get('results', [])

        self.results = []

        for place in places:
            local_list = []
            local_list.append(place.get('name'))
            local_list.append(place.get('admin1'))
            local_list.append(place.get('country'))
            local_list.append(place.get('latitude'))
            local_list.append(place.get('longitude'))

            self.results.append(local_list)

        
        if reply.error() == QNetworkReply.NoError:
            if len(self.results) == 0:
                no_results = text("No results found.", "white", poppins("semi bold"), 14, parent=self.suggestions, transparency=True)
                self.suggestions_layout.addWidget(no_results, alignment=Qt.AlignCenter)
        

            for i in range(8):
                if i < len(self.results):
                    location = self.results[i][0]
                    area = self.results[i][1]
                    country = self.results[i][2]
                    lat = self.results[i][3]
                    lon = self.results[i][4]
                    string = f'{location}, {area}, {country}'
                    coords = [lat, lon]
                else:
                    break

                btn = self.location_hover_button(string)
                if change_type == "change":
                    btn.mousePressEvent = lambda event, c=coords, l=location: self.change_location(event, c, loc_name=l)
                else:
                    def select_location(event, c=coords, n=location):
                        self.add_coords = c
                        self.add_name = n

                        if hasattr(self, 'searchpop') and self.searchpop:
                            self.searchpop.exit_popup()

                        self.add_card(event)

                    btn.mousePressEvent = lambda event, c=coords, n=location: select_location(event, c, n)

                self.suggestions_layout.setAlignment(Qt.AlignTop)
                self.suggestions_layout.addWidget(btn)

        else:
            no_results = text("No results found.", "white", poppins("semi bold"), 14, parent=self.suggestions, transparency=True)
            self.suggestions_layout.addWidget(no_results, alignment=Qt.AlignCenter)

        QApplication.processEvents()
        QTimer.singleShot(50, self.suggestions.updatePixmap)

    def change_location(self, event, coords, loc_name=None):
        self.target_location = loc_name
        self.results = None

        if hasattr(self, 'searchpop') and self.searchpop:
            self.searchpop.exit_popup()

        if hasattr(self, 'timer') and self.timer is not None:
            self.timer.stop()

        hide_viewport = QGraphicsOpacityEffect()
        hide_viewport.setOpacity(0.0)

        self.weather_fade_effect.setOpacity(0.0)
        self.bg_fade_effect.setOpacity(1.0)

        self.bg_fade_out = QPropertyAnimation(self.weather_fade_effect, b'opacity')
        self.bg_fade_out.setDuration(600)
        self.bg_fade_out.setStartValue(self.weather_fade_effect.opacity())
        self.bg_fade_out.setEndValue(0.0)
        self.bg_fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        self.bg_fade_out.start()

        self.viewport.setGraphicsEffect(hide_viewport)

        if self.viewport is not None:
            while self.viewport.layout().count():
                item = self.viewport.layout().takeAt(0)
                widget = item.widget()
                if widget or widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    while item.layout().count():
                        sub = item.layout().takeAt(0)
                        if sub.widget or sub.widget() is not None:
                            sub.widget().deleteLater()
            QWidget().setLayout(self.viewport.layout())
        
        self.location = (coords[0], coords[1])

        

        self.loading = Loading_Icon("./Icons/loading.svg", 64 )
        self.loading.setParent(self.centralwidget)
        self.loading.move((self.width()-self.loading.width())//2, (self.height()-self.loading.height())//2)

        self.load_fade = QGraphicsOpacityEffect(self.loading)
        self.load_fade.setOpacity(1.0)
        self.loading.show()
        self.loading.raise_()
        self.loading.setGraphicsEffect(self.load_fade)

        self.new_weather = WeatherWait(self.location)
        self.new_weather.data.connect(self.loaded)
        self.new_weather.error.connect(self.error)
        self.new_weather.start()
        self.new_weather.finished.connect(self.loading.hide)

        self.first_load = False
        self.initial_place = False

        show_viewport = QGraphicsOpacityEffect()

        show_viewport.setOpacity(1.0)   

        self.viewport.setGraphicsEffect(show_viewport)

        QApplication.processEvents()

    def settings(self, event):
        if not hasattr(self, 'settingspop') or self.settingspop == None:
            self.settingspop = Popup(self)
            self.settingspop.destroyed.connect(lambda: setattr(self, 'settingspop', None))
            
            def cleanup():
                self.settingspop = None 
                self.settings_card = None
                self.temp_radio = None
                self.theme_radio = None
                self.length_radio = None

            
            self.settingspop.destroyed.connect(cleanup)

            self.settings_card = Card(self.settingspop, self.element, 400, raise_dark=False, radius=45)
            self.settings_card.setFixedWidth(700)

            theme = check_theme()

            self.settingspop.popup_layout.addWidget(self.settings_card)

            self.settingslayout = QVBoxLayout(self.settings_card)
            self.settingslayout.setContentsMargins(50, 20, 50, 20)

            current = load_settings()

            temp = 0 if current['units']['temperature'] == "C" else 1
            length = 0 if current['units']['length'] == 'MM' else 1

            self.temp_radio = RadioButton(self.settings_card, "Temperature", options=["Celsius", "Fahrenheit"], selected=temp, element=self.element, functions=[lambda: (update_settings('units', 'temperature', 'C'), self.unit_change()), lambda: (update_settings('units', 'temperature', 'F'), self.unit_change())])
            self.settingslayout.addWidget(self.temp_radio)

            self.theme_radio = RadioButton(self.settings_card, "Theme", options=["Dark", "Light"], selected=theme, element=self.element, functions=[lambda: update_settings('theme', 'main', 'dark'), lambda: update_settings('theme', 'main', 'light')])
            self.theme_radio.valueChanged.connect(self.apply_theme)
            self.settingslayout.addWidget(self.theme_radio)

            self.length_radio = RadioButton(self.settings_card, "Unit System", options=["Metric", "Imperial"], selected=length, element=self.element, functions=[lambda: (update_settings('units', 'length', 'MM'), update_settings('units', 'speed', 'KMH'), self.unit_change()), lambda: (update_settings('units', 'length', 'IN'), update_settings('units', 'speed', 'MPH'), self.unit_change())])
            self.settingslayout.addWidget(self.length_radio)

            self.credits = hover_text(self.settings_card, self.element, "Open Credits", 10)
            self.credits.mousePressEvent = self.open_credits
            self.settingslayout.addWidget(self.credits, alignment=Qt.AlignCenter)

            self.apply_theme(theme)

            QApplication.processEvents()

            self.settings_card.show()
            self.settingspop.show()

            self.settings_card.updatePixmap()
    
    def apply_theme(self, index):
        cards_to_change = [
            self.menu_card,
            self.hourly_forecast,
            self.daily_forecast, 
            self.uvf,
            self.has,
            self.insights_card,
            self.weather_map_card,
        ]

        self.load_map_async(index)

        if hasattr(self, 'search_bar') and self.search_bar and not sip.isdeleted(self.search_bar):
            cards_to_change.append(self.search_bar)
        if hasattr(self, 'suggestions') and self.suggestions and not sip.isdeleted(self.suggestions):
            cards_to_change.append(self.suggestions)

        for card in cards_to_change:
            if card is not None:
                card.alternate(index)
                card.updatePixmap()

        if hasattr(self, 'settings_card') and self.settings_card is not None:
            if index == 0: 
                self.settings_card.dark.setStyleSheet('''
                        background: rgba(0,0,0,50);
                        border-radius: 45px;                      
                ''')
                if getattr(self, 'temp_radio', None): self.temp_radio.radio_card.dark.setStyleSheet("background: rgba(0,0,0,70); border-radius: 35px;")
                if getattr(self, 'theme_radio', None): self.theme_radio.radio_card.dark.setStyleSheet("background: rgba(0,0,0,70); border-radius: 35px;")
                if getattr(self, 'length_radio', None): self.length_radio.radio_card.dark.setStyleSheet("background: rgba(0,0,0,70); border-radius: 35px;")
                if getattr(self, 'credits', None): self.credits.dark.setStyleSheet("background: rgba(0,0,0,70); border-radius: 20px;")
            
            else:
                self.settings_card.dark.setStyleSheet('''
                        background: rgba(255,255,255,10);
                        border-radius: 45px;                      
                ''')

                if getattr(self, 'temp_radio', None): self.temp_radio.radio_card.dark.setStyleSheet("background: rgba(255,255,255,30); border-radius: 35px;")
                if getattr(self, 'theme_radio', None): self.theme_radio.radio_card.dark.setStyleSheet("background: rgba(255,255,255,30); border-radius: 35px;")
                if getattr(self, 'length_radio', None): self.length_radio.radio_card.dark.setStyleSheet("background: rgba(255,255,255,30); border-radius: 35px;")
                if getattr(self, 'credits', None): self.credits.dark.setStyleSheet("background: rgba(255,255,255,30); border-radius: 20px;")

            self.settings_card.updatePixmap()
            if getattr(self, 'temp_radio', None): self.temp_radio.radio_card.updatePixmap()
            if getattr(self, 'theme_radio', None): self.theme_radio.radio_card.updatePixmap()
            if getattr(self, 'length_radio', None): self.length_radio.radio_card.updatePixmap()
            if getattr(self, 'credits', None): self.credits.updatePixmap()
        
        QApplication.processEvents()
    
    def load_map_async(self, index):
        map_thread = QThread(self)
        map_worker = MapWorker(self.location, "light", self.precise)
        map_worker.moveToThread(map_thread)
        
        self.active_threads.append(map_thread)
        
        map_thread.started.connect(map_worker.run)
        map_worker.finished.connect(self.on_map)

        map_worker.finished.connect(map_thread.quit)
        map_worker.finished.connect(map_worker.deleteLater)
        map_thread.finished.connect(map_thread.deleteLater)

        map_thread.finished.connect(lambda: self.active_threads.remove(map_thread) if map_thread in self.active_threads else None)

        map_thread.start()
    
    def on_map(self, pix):
        self.map_label.setPixmap(pix)


    def unit_change(self, index=None):
        QTimer.singleShot(0, self.apply_unit_change)

    def apply_unit_change(self):
        global LENGTH_UNIT, SPEED_UNIT

        unit = load_settings()
        LENGTH_UNIT = unit['units']['length']
        SPEED_UNIT = unit['units']['speed']

        self.status_bar()


        is_fahrenheit = unit['units']['temperature'] == "F"
        
        if hasattr(self, 'raw_dew'):
            if is_fahrenheit:
                self.dew_point = round((self.raw_dew*9)/5+32)
            else:
                self.dew_point = int(self.raw_dew)

        dew_string = f"Dew Point at {self.dew_point}\u00b0"
        if hasattr(self, 'dew_point_text') and not sip.isdeleted(self.dew_point_text):
            self.dew_point_text.setText(dew_string)

        if hasattr(self, 'timeline'):
            while self.timeline.count():
                child = self.timeline.takeAt(0)
                wid = child.widget()
                if wid is not None:
                    wid.deleteLater()
            self.populate_hourly_forecast(self.weather_hourly_forecast_data)


        if hasattr(self, 'daily_layout'):
            while self.daily_layout.count():
                child = self.daily_layout.takeAt(0)
                wid = child.widget()
                if wid is not None:
                    wid.deleteLater()
            self.populate_daily_forecast(self.weather_daily_forecast_data)
            
        if hasattr(self, 'uvf_layout'):
            while self.uvf_layout.count():
                child = self.uvf_layout.takeAt(0)
                wid = child.widget()
                if wid is not None:
                    wid.deleteLater()
            self.populate_uvf()

        if hasattr(self, 'has_layout'):
            while self.has_layout.count():
                child = self.has_layout.takeAt(0)
                wid = child.widget()
                if wid is not None:
                    wid.deleteLater()
            self.populate_has()

        QApplication.processEvents()
        
        if hasattr(self, 'hourly_forecast'): self.hourly_forecast.updatePixmap()
        if hasattr(self, 'daily_forecast'): self.daily_forecast.updatePixmap()
        if hasattr(self, 'uvf'): self.uvf.updatePixmap()
        if hasattr(self, 'has'): self.has.updatePixmap()


    def refresh_dashboard_data(self):
        try:
            with open("./dashboard.json", "r") as d:
                dash_config = json.load(d)
        except Exception as e:
            print(e)

        locs = []

        for i in range(1,6):
            card_info = dash_config.get(f"card{i}")
            if isinstance(card_info, dict) and "lat" in card_info and "lon" in card_info:
                locs.append([card_info.get("lat", 0), card_info.get("lon", 0)])
            else:
                locs.append([0, 0])
        
        self.dash_wait = DashboardWeatherWait(locs[0], locs[1], locs[2], locs[3], locs[4])
        self.dash_wait.data.connect(self.dash_data_loaded)
        self.dash_wait.start()

    def dashboard(self, event):
        global low, hi
        if not hasattr(self, 'dashboardpop') or self.dashboardpop == None:
            self.dashboardpop = Popup(self, clear=False)
            self.dashboardpop.destroyed.connect(lambda: setattr(self, 'dashboardpop', None))
            self.dashboardpop.installEventFilter(self)

            self.selected = []

            theme = check_theme()
            if theme == 0: opaque_element=QPixmap("./Backgrounds/dark-element.png")
            else: opaque_element=QPixmap("./Backgrounds/light-element.png")

            self.yv = 0

            try:
                with open('./dashboard.json', 'r') as d:
                    dash = json.load(d)
                    self.dash_data = dash
            except:
                dash = []

            def cleanup():
                if sip.isdeleted(self):
                    return

                sorted_c = sorted(self.dash_cards, key=lambda c: c.index)

                filled = []

                for card in sorted_c:
                    if hasattr(card, 'location_name'):
                        if isinstance(card.location_name, QLabel):
                            loc_text = card.location_name.text().strip()
                        else:
                            loc_text = str(card.location_name).strip()

                        if loc_text:
                            filled.append({
                                "location_name": loc_text,
                                "lat": getattr(card, 'lat', 0),
                                "lon": getattr(card, 'lon', 0),
                            })
                
                new_dash_data = {}
                
                for idx, data in enumerate(filled, start=1):
                    new_dash_data[f"card{idx}"] = data

                try:
                    with open('./dashboard.json', 'w') as d:
                        json.dump(new_dash_data, d)
                except Exception as e:
                    print(e)

                self.dashboardpop = None
                self.dash_cards = []

                self.yv = 0

                for i in range(1,6):
                    if hasattr(self, f'card{i}'):
                        delattr(self, f'card{i}')

            self.dashboardpop.destroyed.connect(cleanup)
            
            self.dashboard_container = QWidget(self.dashboardpop)
            self.dashboard_container.setGeometry(64,0,750,1400)
            self.dashboard_container.setStyleSheet("background: transparent;")

            self.dashboard_layout = QVBoxLayout(self.dashboard_container)
            self.dashboard_layout.setContentsMargins(25,50,25,50)
            self.dashboard_layout.setSpacing(15)
            self.dashboard_layout.setAlignment(Qt.AlignTop)

            self.dash_cards = [] if not hasattr(self, 'dash_cards') else self.dash_cards
            self.selected_card = None
            
            
            if not self.dash_cards:
                cards_to_load = []
                if isinstance(dash, dict):
                    for i in range(1,6):
                        c_info = dash.get(f"card{i}")
                        if isinstance(c_info, dict) and str(c_info.get("location_name", "")).strip():
                            cards_to_load.append(c_info)
                elif isinstance(dash, list):
                    for c_info in dash:
                        if isinstance(c_info, dict) and str(c_info.get("location_name", "")).strip():
                            cards_to_load.append(c_info)

                for idx, card_info in enumerate(cards_to_load, start=1):
                    loc_name = str(card_info.get("location_name", "")).strip()
                    if not loc_name:
                        continue

                    if hasattr(self, 'dash_weather') and (idx-1) < len(self.dash_weather):
                        current_weather = self.dash_weather[idx-1][1]
                        current_temp = self.dash_weather[idx-1][2]
                        current_desc = self.dash_weather[idx-1][5]
                        
                        try:
                            hi = self.dash_weather[idx-1][3]
                        except IndexError:
                            pass

                        try: 
                            low = self.dash_weather[idx-1][4]
                        except IndexError:
                            pass

                        try:
                            ismorning = self.dash_weather[idx-1][6]
                        except IndexError:
                            pass

                    else:
                        current_weather = "..."
                        current_temp = "--"
                        hi = "--"
                        low = "--"
                        ismorning = True
                    
                    card = WeatherCard(self.dashboard_container, opaque_element, location_name=loc_name, current_condition=current_weather, current_temp=current_temp, hi=hi, low=low, description=current_desc, morning=ismorning)

                    card.location_name = card_info.get("location_name", "")
                    card.lat = card_info.get("lat", 0)
                    card.lon = card_info.get("lon", 0)

                    card.index = i-1
                    card.dragging = False
                    card.drag_start_pos = None
                    card.original_y = 0

                    card.mousePressEvent = lambda event, c=card: self.card_drag_press(event, c)
                    card.mouseMoveEvent = lambda event, c=card: self.card_drag_move(event, c)
                    card.mouseReleaseEvent = lambda event, c=card: self.card_drag_release(event, c)

                    card.updatePixmap()

                    setattr(self, f'card{i}', card)

                    self.dash_cards.append(card)
                
                    self.dashboard_layout.addWidget(card, alignment=Qt.AlignCenter)

                    if card:
                        self.dashboard_layout.addWidget(card, alignment=Qt.AlignCenter)

                if hasattr(self, 'dash_cards') and self.dash_cards:
                    active_count = len(self.dash_cards)
                elif isinstance(dash, list):
                    active_count = sum(1 for c in dash if isinstance(c, dict) and str(c.get("location_name", "")).strip())
                elif isinstance(dash, dict):
                    active_count = sum(1 for i in range(1,6) if isinstance(dash.get(f"card{i}"), dict) and str(dash.get(f"card{i}").get("location_name", "")).strip())  
                else:
                    active_count = 0

                if active_count < 5:
                    add = Card(self.dashboard_container, opaque_element, 200, raise_dark=False)
                    self.add_card_btn = add
                    add.setFixedWidth(600)
                    add.setCursor(Qt.PointingHandCursor)

                    add_layout = QVBoxLayout(add)
                    add_layout.setContentsMargins(0,0,0,0)
                    add_layout.setSpacing(0)

                    add_icon = svg("./Icons/add-circle-dark.svg" if check_theme() == 0 else "./Icons/add-circle-light.svg", 100, 100)
                    add_icon.setCursor(Qt.PointingHandCursor)
                    add_icon.mousePressEvent = lambda event: self.search(event, change=False)
                    add_layout.addWidget(add_icon, alignment=Qt.AlignCenter)
                    add.updatePixmap()
                    
                    self.dashboard_layout.addWidget(add, alignment=Qt.AlignCenter)
                
                    self.check_add_btn()
            
            QApplication.processEvents()
            self.dashboard_container.show()

        else:
            for card in self.dash_cards:
                if card is not sip.isdeleted(card):
                    card.updatePixmap()
            if hasattr(self, 'add_card_btn') and self.add_card and not sip.isdeleted(self.add_card_btn):
                self.add_card_btn.updatePixmap()

    def update_dashboard(self):
        if not hasattr(self, 'dash_cards') or not self.dash_cards:
            return
        
        data = getattr(self, 'dash_weather_data', {})

        for idx, card in enumerate(self.dash_cards, start=1):
            current_key = f'current{idx}'
            hi_lo_key = f'hi_lo{idx}'

            if current_key not in data:
                continue
            
            current_info = data.get(current_key, {})
            hi_lo_info = data.get(hi_lo_key, {})

            weather_list = current_info.get("weather", [])
            
            if weather_list and isinstance(weather_list[0], dict):
                condition_id = weather_list[0].get("id", "N/A")
                condition_main = weather_list[0].get("main", "N/A")
                desc = weather_list[0].get("description", "N/A")
            else:
                condition = "N/A"
                desc = "N/A"

            main_data = current_info.get("main", {})
            temp = main_data.get("temp", "N/A") if isinstance(main_data, dict) else "N/A"

            sys_data = current_info.get("sys", {})
            card.ismorning = sys_data.get("sunrise", 0) <= datetime.datetime.now(datetime.timezone.utc).timestamp() < sys_data.get("sunset", 0)

            daily_max = hi_lo_info.get("daily", {}).get('temperature_2m_max', 0)
            daily_min = hi_lo_info.get("daily", {}).get('temperature_2m_min', 0)

            temp_max = round(daily_max[0]) if daily_max else "N/A"
            temp_min = round(daily_min[0]) if daily_min else "N/A"
            current_temp = round(temp) if isinstance(temp, (int,float)) else "N/A"

            if hasattr(card, "condition_label"):
                card.condition_label.setText(str(condition_main))
                card.cond = str(condition_main)
                card.description = str(desc) 
                card.current_condition = condition_id
                card.updateWeatherBG()
            if hasattr(card, "temp_label"):
                card.temp_label.setText(f"{current_temp}\u00b0")
            if hasattr(card, 'hi_lo_label'):
                card.hi_lo_label.setText(f"H: {temp_max}\u00b0 L: {temp_min}\u00b0")
 
            daily_min_list = hi_lo_info.get("daily", {}).get('temperature_2m_min', [])
            daily_max_list = hi_lo_info.get("daily", {}).get('temperature_2m_max', [])

            hi = str(int(daily_max_list[0])) if daily_max_list else "N/A"
            low = str(int(daily_min_list[0])) if daily_min_list else "N/A"


        
    def save_dashboard(self):
        self.dash_cards.sort(key=lambda c: c.index)

        new_dash_data = {}
        for idx, data in enumerate(self.dash_cards, start=1):
            loc_attr = getattr(data, 'location_name', " ")

            if isinstance(loc_attr, QLabel):
                loc_name = loc_attr.text()
            else:
                loc_name = str(loc_attr)
            
            lat = float(getattr(data, 'lat', 0.0))
            lon = float(getattr(data, 'lon', 0.0))
            
            new_dash_data[f"card{idx}"] = {
                "location_name": loc_name,
                "lat": data.lat,
                "lon": data.lon,
            }

        self.dash_data = new_dash_data

        try:
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.json")
        except:
            json_path = "./dashboard.json"
    
        try:
            with open(json_path, 'w') as d:
                json.dump(self.dash_data, d, indent=4)
        except Exception as e:
            print("Error dumping data")
            print(e)

    def add_card(self, event):
        if hasattr(self, 'add_coords') and self.add_coords:
            lat, lon = self.add_coords[0], self.add_coords[1]
            
            count = len(self.dash_data)

            if count > 6:
                return
            
            opaque_element = QPixmap("./Backgrounds/dark-element.png") if check_theme() == 0 else QPixmap("./Backgrounds/light-element.png")


            if hasattr(self, 'add_name') and self.add_name:
                location = self.add_name
            elif hasattr(self, 'results') and self.results:
                location = self.results[0][0]
            

            card = WeatherCard(self.dashboard_container, opaque_element, location, current_condition="----", current_temp="--", hi="--", low="--")
            card.index = count
            card.dragging = False
            card.lat = lat
            card.lon = lon
            card.index = count
            card.drag_start_pos = None
            card.original_y = 0

            card.mousePressEvent = lambda event, c=card: self.card_drag_press(event, c)
            card.mouseMoveEvent = lambda event, c=card: self.card_drag_move(event, c)
            card.mouseReleaseEvent = lambda event, c=card: self.card_drag_release(event, c)

            card.updatePixmap()

            self.dash_cards.append(card)

            if hasattr(self, 'add_card_btn') and self.add_card and not sip.isdeleted(self.add_card_btn):
                self.dashboard_layout.removeWidget(self.add_card_btn)
            
            self.dashboard_layout.addWidget(card, alignment=Qt.AlignCenter)

            if len(self.dash_cards) < 5 and hasattr(self, 'add_card_btn') and self.add_card_btn and not sip.isdeleted(self.add_card_btn):
                self.dashboard_layout.addWidget(self.add_card_btn, alignment=Qt.AlignCenter)
            elif len(self.dash_cards) >= 5 and hasattr(self, 'add_card_btn') and self.add_card_btn and not sip.isdeleted(self.add_card_btn):
                self.add_card_btn.hide()

            self.save_dashboard()
            self.refresh_dashboard_data()

    def check_add_btn(self):
        if hasattr(self, 'add_card_btn') and self.add_card_btn and not sip.isdeleted(self.add_card_btn):
            if len(self.dash_cards) < 5:
                self.add_card_btn.show()
                self.add_card_btn.raise_()
                self.add_card_btn.updatePixmap()
            else:
                self.add_card_btn.hide()

    def rebuild_dash(self):
        for i in reversed(range(self.dashboard_layout.count())):
            item = self.dashboard_layout.itemAt(i)
            if item.widget():
                self.dashboard_layout.removeWidget(item.widget())
        
        for idx, card in enumerate(self.dash_cards):
            card.index = idx
            self.dashboard_layout.addWidget(card, alignment=Qt.AlignCenter)

        if hasattr(self, 'add_card_btn') and self.add_card_btn and not sip.isdeleted(self.add_card_btn):
            self.dashboard_layout.addWidget(self.add_card_btn, alignment=Qt.AlignCenter)

        self.check_add_btn()

    def card_drag_press(self, event, card):
        if event.button() == Qt.LeftButton:
            card.dragging = True
            card.dragging_unlocked = False
            card.drag_start_pos = event.globalPos()
            card.original_y = card.y()
            card.original_x = card.x()
            card.swipe = False
            card.vertical_swipe = False

            if not hasattr(card, 'hold_timer'):
                card.hold_timer = QTimer()
                card.hold_timer.setSingleShot(True)

                def unlock():
                    card.dragging_unlocked = True
                    card.dragging = True
                    card.swipe = False
                    card.vertical_swipe = False
                    card.raise_()
                    card.setCursor(Qt.ClosedHandCursor)

                card.hold_timer.timeout.connect(unlock)

            card.hold_timer.start(200)

    def card_drag_move(self, event, card):
        if not getattr(card, 'dragging', False) or not getattr(card, 'dragging_unlocked', False):   
            return
        
        delta = event.globalPos() - card.drag_start_pos
        
        if not card.swipe and not card.vertical_swipe:
            if abs(delta.x()) > abs(delta.y()) and abs(delta.x()) > 5:
                card.swipe = True
            elif abs(delta.y()) > abs(delta.x()) and abs(delta.y()) > 5:
                card.vertical_swipe = True

        if card.swipe:
            new_x = card.original_x + delta.x()
            new_y = card.original_y
        elif card.vertical_swipe:
            new_x = card.original_x
            new_y = card.original_y + delta.y()
        else:
            new_x = card.original_x + delta.x()
            new_y = card.original_y + delta.y()

        if new_x < card.original_x:
            new_x = card.original_x

        rowh = card.height() + 15
        min_y = 50
        max_y = ((len(self.dash_cards) - 1) * rowh) + 50
        new_y = max(min_y, min(new_y, max_y))
        
        card.move(new_x, new_y)

        card_pos = card.mapTo(self.dashboardpop, QPoint(0,0))
        card_bottom_in_pop = card_pos.y() + card.height()
        scrolling_speed = 10

        if card_bottom_in_pop > (self.dashboardpop.height() - 40):
            if self.yv > -620:
                self.yv -= scrolling_speed
            if self.yv < -620:
                self.yv = -620
            
            self.dashboard_container.move(self.dashboard_container.x(), int(self.yv))
            card.drag_start_pos.setY(card.drag_start_pos.y()+scrolling_speed)
            card.original_y -= scrolling_speed
        
        elif card_pos.y() < 40:
            if self.yv < 0:
                self.yv += scrolling_speed
            if self.yv > 0:
                self.yv = 0
            
            self.dashboard_container.move(self.dashboard_container.x(), int(self.yv))   
            card.drag_start_pos.setY(card.drag_start_pos.y()-scrolling_speed)
            card.original_y += scrolling_speed
        
        if card in self.dash_cards:
            current = self.dash_cards.index(card)
            rowh = card.height()+15

            if current > 0 and new_y < (current * rowh) - (rowh/2):
                # Kinda like a neighbor checking
                self.dash_cards[current], self.dash_cards[current - 1] = self.dash_cards[current - 1], self.dash_cards[current]
                
                for idx, c in enumerate(self.dash_cards):
                    c.index = idx
                    target_y = (idx * rowh) + 50
                    if c != card:
                        self.glide(c, target_y)

            
            elif current < len(self.dash_cards) - 1 and new_y > (current * rowh) + (rowh / 2):
                self.dash_cards[current], self.dash_cards[current+1] = self.dash_cards[current+1], self.dash_cards[current]
                
                for idx, c in enumerate(self.dash_cards):
                    c.index = idx
                    target_y = (idx * rowh) + 50
                    if c != card:
                        self.glide(c, target_y)

            else:
                pass


    def card_drag_release(self, event, card):
        if hasattr(card, 'hold_timer'):
            card.hold_timer.stop()
        
        if not getattr(card, 'dragging_unlocked', False): 
            loc_name = card.location_name.text() if isinstance(card.location_name, QLabel) else str(card.location_name)

            self.change_location(event, (card.lat, card.lon), loc_name=loc_name)
            self.dashboardpop.exit_popup()
            card.dragging = False
            card.dragging_unlocked = False
            return

        if card.dragging:
            card.dragging = False
            card.setCursor(Qt.OpenHandCursor)

            if card.x() - card.original_x > 150:
                self.dismiss_card(card)
                return

            rowh = card.height() + 15
            target_y = (card.index * rowh) + 50
            
            self.glide(card, target_y, target_x=card.original_x)

            QTimer.singleShot(210, self.rebuild_dash)
            self.save_dashboard()



    def dismiss_card(self, card):
        mapped_pos = card.mapTo(self.dashboardpop, QPoint(0,0))

        card.placeholder = QWidget()
        card.placeholder.setFixedSize(card.size())

        idx = self.dashboard_layout.indexOf(card)
        if idx != -1:
            self.dashboard_layout.insertWidget(idx, card.placeholder, alignment=Qt.AlignCenter)

        self.dashboard_layout.removeWidget(card)

        card.setParent(self.dashboardpop)
        card.move(mapped_pos)
        card.show()
        card.raise_()

        end_x = self.dashboardpop.width()+100
        end_pos = QPoint(end_x, mapped_pos.y())

        card.anim = QPropertyAnimation(card, b'pos')
        card.anim.setDuration(250)
        
        card.anim.setStartValue(mapped_pos)
        card.anim.setEndValue(end_pos)
        
        card.anim.setEasingCurve(QEasingCurve.InOutQuad)

        def slide_finished():
            if self.yv < 0:
                self.yv = min(0, self.yv+215)
                self.dashboard_container.move(self.dashboard_container.x(), int(self.yv))

            if card in self.dash_cards:
                self.dash_cards.remove(card)
            
            if hasattr(card, 'placeholder') and card.placeholder:
                self.dashboard_layout.removeWidget(card.placeholder)
                card.placeholder.deleteLater()
                card.placeholder = None
            
            card.deleteLater()

            rowh = 215

            for idx, c in enumerate(self.dash_cards):
                c.index = idx
                target_y = (idx * rowh) + 50
                self.glide(c, target_y)

            self.check_add_btn()
            if hasattr(self, 'add_card_btn') and self.add_card and not sip.isdeleted(self.add_card_btn):
                add_btn_target = (len(self.dash_cards) * rowh) + 50
                self.glide(self.add_card_btn, add_btn_target)

            QTimer.singleShot(225, self.check_add_btn)
            self.save_dashboard()

        card.anim.finished.connect(slide_finished)
        card.anim.start()

    
    def glide(self, card, target_y, duration=200, target_x=None):
        if hasattr(card, 'anim') and card.anim is not None:
            card.anim.stop()
        
        end_x = card.x() if target_x is None else int(target_x)
        
        card.anim = QPropertyAnimation(card, b'pos')
        card.anim.setDuration(duration)
        
        card.anim.setStartValue(card.pos())
        card.anim.setEndValue(QPoint(end_x,  int(target_y)))
        
        card.anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        card.anim.start()


    def hide(self, event, card):
            card.highlight.hide()
            if hasattr(self, 'move_menu') and self.move_menu is not None and not sip.isdeleted(self.move_menu):
                self.move_menu.hide()
                self.move_menu.destroy()

    def location_hover_button(self, text_l):
        container = QFrame()
        container.setCursor(Qt.PointingHandCursor)

        text_l = str(text_l)

        container.setStyleSheet('''
                                
            QFrame {
                background: transparent;
                border-radius: 12px;
            }
                                
            QFrame:hover {
                background: rgba(255,255,255,30);                    
            }

        ''')

        label = text(text_l, "white", poppins("semi bold"), 14, container)
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        area_layout = QHBoxLayout(container)
        area_layout.setContentsMargins(15,4,15,4)
        area_layout.addWidget(label, alignment=Qt.AlignLeft)

        return container
        

    def daily(self):
        if len(self.weather_daily_forecast_data) > 5:
            self.viewport.setGeometry(0, 0, 878, 2390)
            self.viewport.update()
        self.daily_forecast = Card(self.viewport, self.element, 590 if len(self.weather_daily_forecast_data) > 5 else 490, rain_effect=True if "rain" in self.current_condition.lower() else False)
        self.daily_forecast.setContentsMargins(35,0,0,0)
        self.daily_layout = QVBoxLayout(self.daily_forecast)
        self.populate_daily_forecast(self.weather_daily_forecast_data)
        
    def populate_daily_forecast(self, forecast_data):
        # Scale Values
        num_pad = 5

        self.daily_layout.setAlignment(Qt.AlignLeft)
        self.daily_layout.setSpacing(0)
        
        data = self.weather_daily_forecast_data

        unit = load_settings()
        is_fahrenheit = unit['units']['temperature'] == "F"
        is_mph = unit['units']['speed'] == "MPH"
        
        for i in range(len(data)):
            horizontal_widget = QWidget()
            horizontal_widget.setFixedHeight(90)
            
            hbox = QHBoxLayout(horizontal_widget)
            hbox.setContentsMargins(5,0,0,0)
            hbox.setSpacing(25)
            print(self.current_weather_id)
            
            cond = data[i][1]

            if cond == 800:
                cond = svg("./Icons/clear-day.svg", 64, 64)
            elif cond == 804:
                cond = svg("./Icons/cloudy.svg", 64, 64)
            elif cond in (801, 802, 803):
                cond = svg("./Icons/partly-cloudy-day.svg", 64, 64)
            elif cond in (500, 501, 502, 503, 504, 520, 521, 522, 531):
                if cond == 500:
                    cond = svg("./Icons/drizzle.svg", 64, 64)
                else:
                    cond = svg("./Icons/rain.svg", 64, 64)
            elif cond in (200, 201, 202, 210, 211, 212, 221, 230, 231, 232):
                cond = svg("./Icons/thunderstorm.svg", 64, 64)
            elif cond in (300, 301, 302, 310, 311, 312, 321):
                cond = svg("./Icons/drizzle.svg", 64, 64)
            elif cond in (600, 601, 602, 611, 612, 615, 616, 620, 621, 621):
                cond = svg("./Icons/snowflake.svg", 64, 64)
            elif cond == 611:
                cond = svg("./Icons/hail.svg", 64, 64)
            elif cond == 721:
                cond = svg("./Icons/haze.svg", 64, 64)
            elif cond == 731:
                cond = svg("./Icons/dust.svg", 64, 64)
            elif cond in (701, 741):
                cond = svg("./Icons/fog.svg", 64, 64)
            else:
                print(f"No icon for {cond}")
                return
            
            
            cond.setStyleSheet("padding-bottom: 8px;")
            cond.setFixedWidth(64)
            hbox.addWidget(cond)
            
            day = data[i][0]
            day = text(day if i != 0 else "Today", "white", poppins("semi bold"), 20, horizontal_widget)
            day.setFixedWidth(200)
            day.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            if is_fahrenheit:
                min_max = data[i][2], data[i][3]
            else:
                min_max = round((int(data[i][2])-32)*5/9), round((int(data[i][3])-32)*5/9)
            
            min_max_string = f"{min_max[0]}\u00b0 / {min_max[1]}\u00b0"
            min_max = text(min_max_string, "white", poppins("semi bold"), 20, horizontal_widget)
            min_max.setFixedWidth(120)
            min_max.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            if is_mph:
                wind_speed = data[i][5]
                SPEED_UNIT = "MPH"
            else:
                wind_speed = round(int(data[i][5])*1.6)
                SPEED_UNIT = "KMH"


            if int(data[i][4]) == 0:
                end_icon = svg("./Icons/wind.svg", 51, 51)
                num = text(str(wind_speed)+" "+SPEED_UNIT, "white", poppins("semi bold"), 17, horizontal_widget)
                num.setFixedWidth(85)
            else:
                end_icon = svg("./Icons/raindrop.svg", 56, 56)
                #end_icon.setFixedWidth(65)
                num = text(str(data[i][4])+" %", "white", poppins("semi bold"), 17, horizontal_widget)
                num.setFixedWidth(78)
                num.setStyleSheet(f"padding-top: {num_pad}px; color: white;")
                
            hbox.addWidget(day)
            hbox.addSpacing(45)
            hbox.addWidget(min_max)
            hbox.addSpacing(65)
            hbox.addWidget(end_icon)
            hbox.addWidget(num)
            self.daily_layout.addWidget(horizontal_widget)
            horizontal_widget.show()

    def insights(self):
        self.insights_card = Card(self.viewport, self.element, 200, rain_effect=True if "rain" in self.current_condition.lower() else False)
        self.insights_card.setContentsMargins(0,0,0,0)
        self.insights_layout = QHBoxLayout(self.insights_card)
        self.insights_layout.setContentsMargins(15,0,15,0)
        self.populate_insights()
    
    def populate_insights(self, data=[]):
        spacing = 12

        self.index = 0

        theme = check_theme()
        
        self.insights_layout.setAlignment(Qt.AlignCenter)
        self.insights_layout.setSpacing(0)

        self.backward = hover_svg("./Icons/forward.svg", 45, 45, reverse=True)
        self.backward.setCursor(Qt.PointingHandCursor)
        self.backward.mousePressEvent = lambda event: self.change_insights(event, f=False)
        self.backward.raise_()

        self.insights_layout.addWidget(self.backward, alignment=Qt.AlignCenter)

        self.insights_layout.addStretch(1)

        self.insight_widget = QWidget(self.insights_card)
        self.insights_widget_layout = QVBoxLayout(self.insight_widget)
        self.insights_widget_layout.setContentsMargins(0,0,0,0)
        self.insights_widget_layout.setSpacing(spacing)

        title = self.insights_list[0][0]
        
        self.insights_title = text(title, "white", poppins("semi bold"), 12, self.insight_widget)
        self.insights_title.setStyleSheet(self.insights_title.styleSheet() + "; color: rgba(255, 255, 255, 0.5);")
        self.insights_widget_layout.addWidget(self.insights_title, alignment=Qt.AlignCenter)

        self.insights_title_fade = QGraphicsOpacityEffect(self.insights_title)
        self.insights_title_fade.setOpacity(1.0)
        self.insights_title.setGraphicsEffect(self.insights_title_fade)

        self.insights_widget_layout.addStretch(1)

        body = self.insights_list[0][1]
        

        self.insights_body = text(body, "white", poppins("semi bold"), 17, self.insight_widget)
        self.insights_body.setFixedWidth(600)
        self.insights_body.setMinimumHeight(90)
        self.insights_body.setAlignment(Qt.AlignCenter)
        self.insights_body.setWordWrap(True)

        self.insights_body_fade = QGraphicsOpacityEffect(self.insights_body)
        self.insights_body_fade.setOpacity(1.0)
        self.insights_body.setGraphicsEffect(self.insights_body_fade)

        self.insights_widget_layout.addStretch(1)

        self.three_dots = QWidget(self.insight_widget)
        self.three_dots_layout = QHBoxLayout(self.three_dots)
        self.three_dots_layout.setContentsMargins(0,0,0,0)
        
        self.dot1 = svg("./Icons/selector-dot.svg", 25, 25)
        self.dot1opacity = QGraphicsOpacityEffect(self.dot1)
        self.dot1.setGraphicsEffect(self.dot1opacity)
        self.dot1opacity.setOpacity(0.3)

        self.dot2 = svg("./Icons/selector-dot.svg", 25, 25)
        self.dot2opacity = QGraphicsOpacityEffect(self.dot2)
        self.dot2.setGraphicsEffect(self.dot2opacity)
        self.dot2opacity.setOpacity(0.3)

        self.dot3 = svg("./Icons/selector-dot.svg", 25, 25)
        self.dot3opacity = QGraphicsOpacityEffect(self.dot3)
        self.dot3.setGraphicsEffect(self.dot3opacity)
        self.dot3opacity.setOpacity(0.3)

        self.three_dots_layout.addWidget(self.dot1, alignment=Qt.AlignCenter)
        self.three_dots_layout.addWidget(self.dot2, alignment=Qt.AlignCenter)
        self.three_dots_layout.addWidget(self.dot3, alignment=Qt.AlignCenter)

        self.insights_widget_layout.addWidget(self.insights_body, alignment=Qt.AlignCenter)

        self.insights_widget_layout.addWidget(self.three_dots, alignment=Qt.AlignCenter)

        self.insights_layout.addWidget(self.insight_widget, alignment=Qt.AlignCenter)

        self.insights_layout.addStretch(1)

        self.forward = hover_svg("./Icons/forward.svg", 45, 45)
        self.forward.setCursor(Qt.PointingHandCursor)
        self.forward.mousePressEvent = lambda event: self.change_insights(event, f=True)
        self.forward.raise_()

        self.insights_layout.addWidget(self.forward, alignment=Qt.AlignCenter)


        self.insights_card.updatePixmap()

    def change_insights(self, event, f=True):
        if f:
            self.index += 1
        else:
            self.index -= 1
        
        if self.index > 2:
            self.index = 0
        elif self.index < 0:
            self.index = 2

        if self.index == 0:
            self.dot1opacity.setOpacity(1.0)
            self.dot2opacity.setOpacity(0.3)
            self.dot3opacity.setOpacity(0.3)
        elif self.index == 1:
            self.dot1opacity.setOpacity(0.3)
            self.dot2opacity.setOpacity(1.0)
            self.dot3opacity.setOpacity(0.3)
        elif self.index == 2:
            self.dot1opacity.setOpacity(0.3)
            self.dot2opacity.setOpacity(0.3)
            self.dot3opacity.setOpacity(1.0)

        self.update_insights()

    def update_insights(self):
        self.insights_body_fade_anim = QPropertyAnimation(self.insights_body_fade, b'opacity')
        self.insights_body_fade_anim.setDuration(250)
        self.insights_body_fade_anim.setStartValue(1.0)
        self.insights_body_fade_anim.setEndValue(0.0)
        self.insights_body_fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.insights_body_fade_anim.start()

        self.insights_title_fade_anim = QPropertyAnimation(self.insights_title_fade, b'opacity')
        self.insights_title_fade_anim.setDuration(250)
        self.insights_title_fade_anim.setStartValue(1.0)
        self.insights_title_fade_anim.setEndValue(0.0)
        self.insights_title_fade_anim.setEasingCurve(QEasingCurve.InOutQuad)

        def on_fade_out_finished():
            spacing = 12
            body = self.insights_list[self.index][1]
            if len(body) > 95:
                spacing = 14
            self.insights_widget_layout.setSpacing(spacing)

            self.insights_body.setText(body)
            self.insights_title.setText(self.insights_list[self.index][0])

            self.insight_widget.layout().update()
            self.dot1opacity.update()
            self.dot2opacity.update()
            self.dot3opacity.update()
            self.three_dots.repaint()

            if self.index == 0:
                self.dot1.move(self.dot1.x(), self.dot1.y())
            if self.index == 1:
                self.dot2.move(self.dot2.x(), self.dot3.y())
            if self.index == 2:
                self.dot3.move(self.dot3.x(), self.dot2.y())

            self.insights_body_fadein_anim = QPropertyAnimation(self.insights_body_fade, b'opacity')
            self.insights_body_fadein_anim.setDuration(250)
            self.insights_body_fadein_anim.setStartValue(0.0)
            self.insights_body_fadein_anim.setEndValue(1.0)
            self.insights_body_fadein_anim.setEasingCurve(QEasingCurve.InOutQuad)
            self.insights_body_fadein_anim.start()

            self.insights_title_fadein_anim = QPropertyAnimation(self.insights_title_fade, b'opacity')
            self.insights_title_fadein_anim.setDuration(250)
            self.insights_title_fadein_anim.setStartValue(0.0)
            self.insights_title_fadein_anim.setEndValue(1.0)
            self.insights_title_fadein_anim.setEasingCurve(QEasingCurve.InOutQuad)
            self.insights_title_fadein_anim.start()
        
        self.insights_body_fade_anim.finished.connect(on_fade_out_finished) 
        self.insights_body_fade_anim.start()
        

    def hourly(self):
        self.hourly_forecast = Card(self.viewport, self.element, 200, rain_effect=True if "rain" in self.current_condition.lower() else False)
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
            
            is_night = False

            try:
                hourt = datetime.datetime.strptime(str(forecast_data[i][0]), "%I %p").time()
                srt = datetime.datetime.strptime(self.sunrise, "%I:%M %p").time()
                sst = datetime.datetime.strptime(self.sunset, "%I:%M %p").time()

                if hourt < srt or hourt > sst:
                    is_night = True
            except:
                pass

            
            if str(forecast_data[i][1]).lower() == "clear":
                if not is_night:
                    condition = svg("./Icons/clear-day.svg", 83, 83)
                else:
                    condition = svg("./Icons/clear-night.svg", 83, 83)
            elif str(forecast_data[i][1]).lower() == "rain":
                condition = svg("./Icons/rain.svg", 83, 83)
            elif "cloud" in str(forecast_data[i][1]).lower() or "few" in str(forecast_data[i][1]).lower() or "scattered" in str(forecast_data[i][1]).lower():
                if not is_night:
                    condition = svg("./Icons/partly-cloudy-day.svg", 83, 83)
                else:
                    condition = svg("./Icons/partly-cloudy-night.svg", 83, 83)
            elif str(forecast_data[i][1]).lower() == "clouds" or str(forecast_data[i][1]).lower() == "overcast" or str(forecast_data[i][1]).lower() == "cloudy":
                condition = svg("./Icons/cloudy.svg", 83, 83)
            elif str(forecast_data[i][1]).lower() == "snow":
                condition = svg("./Icons/snowflake.svg", 83, 83)
            elif "thunderstorm" in str(forecast_data[i][1]).lower():
                condition = svg("./Icons/thunderstorm.svg", 83, 83)
            elif "fog" in str(forecast_data[i][1]).lower():
                condition = svg("./Icons/fog.svg", 83, 83)
            elif "dust" in str(forecast_data[i][1]).lower():
                condition = svg("./Icons/dust.svg", 83, 83)
            elif "haze" in str(forecast_data[i][1]).lower():
                condition = svg("./Icons/haze.svg", 83, 83)
            elif "light" or "drizzle" in str(forecast_data[i][1]).lower():
                condition = svg("./Icons/rain.svg", 83, 83)
            elif "hail" in str(forecast_data[i][1]).lower():
                condition = svg("./Icons/hail.svg", 83, 83)

            unit = load_settings()
            is_fahrenheit = unit['units']['temperature'] == "F"

            temp_num = forecast_data[i][2]
            temp_c = round((forecast_data[i][2]-32)*5/9)
            
            temp = text(" "+str(temp_num if is_fahrenheit else temp_c)+"\u00b0", "white", poppins("semi bold"), 18, vertical_widget)
            temp.setAlignment(Qt.AlignCenter)
            
            
            vdata.addWidget(time)
            
            vdata.addWidget(condition)
            vdata.addSpacing(8)
            vdata.addWidget(temp)
            vdata.setAlignment(Qt.AlignCenter)
            
            self.timeline.addWidget(vertical_widget)
            vertical_widget.show()
    
    def weather_map(self):
        self.weather_map_card = Card(self.viewport, self.element, 350, rain_effect=True if "rain" in self.current_condition.lower() else False)
        self.weather_map_card.setCursor(Qt.PointingHandCursor)
        self.weather_map_card.dark.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        
        self.map_layout = QVBoxLayout(self.weather_map_card)
        self.map_layout.setContentsMargins(25,20,25,20)
        self.map_layout.setAlignment(Qt.AlignCenter)
        
        self.map_label = QLabel()
        self.map_label.setFixedSize(778, 305)

        self.map_label.setStyleSheet("background: transparent;")
        self.map_label.setScaledContents(False)

        scaled_pix = self.map_pixmap.scaled(778, 305, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        raw_pix = scaled_pix.copy(0,0, 778, 305)

        smooth_pixmap = QPixmap(778, 305)
        smooth_pixmap.fill(Qt.transparent)

        painter = QPainter(smooth_pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, 778, 305), 45, 45)

        painter.setClipPath(path)
        painter.drawPixmap(0, 0, raw_pix)
        painter.end()


        self.map_label.setPixmap(smooth_pixmap)
        
        self.click_event = QPushButton(self.map_label)
        self.click_event.setStyleSheet("background-color: transparent; border: none;")
        self.click_event.clicked.connect(self.popup)
        
        self.click_event.setGeometry(0,0,778,305)

        self.map_layout.addWidget(self.map_label, alignment=Qt.AlignCenter)
        
    def popup(self):
        # Create Popup block
        
        if self.popup_active:
            return
        
        self.timer.stop()
        self.popup_active = True
        
        self.blur = QGraphicsBlurEffect()
        self.blur.setBlurRadius(25)
        self.blur.setBlurHints(QGraphicsBlurEffect.QualityHint)
        self.viewport.setGraphicsEffect(self.blur)
        
        

        self.popup_card = Card(self.centralWidget(), self.element, 500)
        self.popup_card.setFixedWidth(700)
        self.popup_card.bg.hide()
        self.popup_card.dark.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        self.popup_card.move((self.width()-self.popup_card.width())//2, (self.height()-self.popup_card.height())//2)
        

        # Creates map ----------------------
        
        map_layout = QVBoxLayout(self.popup_card)
        map_layout.setContentsMargins(0,0,0,0)
        
        map_widget = QWebEngineView()

        map_widget.setStyleSheet("background: transparent;")   
        map_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        map_widget.page().setBackgroundColor(Qt.transparent)

        settings = map_widget.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)

        self.path = os.path.abspath("./map.html")

        map_widget.setUrl(QUrl.fromLocalFile(self.path))
        map_layout.addWidget(map_widget)
        
        QApplication.processEvents()


        self.popup_card.show()
        self.popup_card.raise_()
        
    def hide_popup(self):
        self.viewport.setGraphicsEffect(None)
        if hasattr(self, "popup_card"):
            if not sip.isdeleted(self.popup_card):
                layout = self.popup_card.layout()
                if layout and layout.count() > 0:
                    map_widget = layout.itemAt(0).widget()
                    if isinstance(map_widget, QWebEngineView):
                        #map_widget.page().profile().clearHttpCache()
                        
                        map_widget.setUrl(QUrl("about:blank"))
                        #map_widget.setPage(None)
                        
                        #map_widget.deleteLater()
                        
                self.popup_card.deleteLater() 
            self.popup_card = None
            self.popup_active = False
            
            gc.collect()
            
        self.timer.start(self.frequency)
    
    def uv_and_feels_like(self):
        self.uvf = Card(self.viewport, self.element, 250, rain_effect=True if "rain" in self.current_condition.lower() else False)
        self.uvf.setContentsMargins(105,20,55,0)
        self.uvf_layout = QVBoxLayout(self.uvf)
        self.uvf_layout.setSpacing(0)
        self.populate_uvf()
    
    def populate_uvf(self):
        column_widget = QWidget()
        column_layout = QHBoxLayout(column_widget)
        column_layout.setContentsMargins(0,0,0,0)
        column_layout.setSpacing(0)
        
        # UV Column
        uv_widget = QWidget()
        uv_layout = QVBoxLayout(uv_widget)
        uv_layout.setContentsMargins(0,0,0,0)
        uv_layout.setSpacing(4)
        
        # Icon & Title (UV)
        
        iwt = QWidget()
        iwt_layout = QHBoxLayout(iwt)
        iwt_layout.setContentsMargins(0,0,0,0)
        iwt_layout.setSpacing(0)
        iwt_layout.addWidget(svg("./Icons/clear-day.svg", 34, 34))
        uv_index_title = text("UV Index", "white", poppins("semi bold"), 15, iwt)
        uv_index_title.setStyleSheet("color: rgba(255, 255, 255, 0.5); padding-top: 5px;")
        iwt_layout.addWidget(uv_index_title)
        
        # ====================
        
        
        uv_layout.addWidget(iwt, alignment=Qt.AlignCenter)
        uv_layout.addStretch(1)
        uv_layout.addWidget(text(str(round(int(self.uv_index))), "white", poppins("semi bold"), 40, uv_widget), alignment=Qt.AlignCenter)
        uv_layout.addStretch(1)

        if round(int(self.uv_index)) <= 2:
            uv_desc = text("Low", "white", poppins("semi bold"), 12, uv_widget)
        elif round(int(self.uv_index)) <= 5 and round(int(self.uv_index)) > 2:
            uv_desc = text("Moderate", "white", poppins("semi bold"), 12, uv_widget)
        elif round(int(self.uv_index)) <= 7 and round(int(self.uv_index)) > 5:
            uv_desc = text("High", "white", poppins("semi bold"), 12, uv_widget)
        elif round(int(self.uv_index)) <= 10 and round(int(self.uv_index)) > 7:
            uv_desc = text("Very High", "white", poppins("semi bold"), 12, uv_widget)
        elif round(int(self.uv_index)) > 10:
            uv_desc = text("Extreme", "white", poppins("semi bold"), 12, uv_widget)
        
        uv_desc.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        uv_layout.addWidget(uv_desc, alignment=Qt.AlignCenter)
        uv_layout.addStretch(1)
        
        
        # Rainfall Column
        rf_widget = QWidget()
        rf_layout = QVBoxLayout(rf_widget)
        rf_layout.setContentsMargins(0,0,0,0)
        rf_layout.setSpacing(4)

        # Icon & Title (Rainfall)
                
        rfw = QWidget()
        rfw_layout = QHBoxLayout(rfw)
        rfw_layout.setContentsMargins(0,0,0,0)
        rfw_layout.setSpacing(0)
        rfw_layout.addWidget(svg("./Icons/raindrop.svg", 38, 38))
        rf_index_title = text("Rainfall", "white", poppins("semi bold"), 15, rfw)
        rf_index_title.setStyleSheet("color: rgba(255, 255, 255, 0.5); padding-top: 5px;")
        rfw_layout.addWidget(rf_index_title)

        # ====================

        rf_layout.addWidget(rfw, alignment=Qt.AlignCenter)
        rf_layout.addStretch(1)

        unit = load_settings()
        is_mm = unit['units']['length'] == "MM"

        if is_mm: LENGTH_UNIT = "MM"
        else: LENGTH_UNIT = "IN"

        
        if LENGTH_UNIT == "MM":
            if int(self.precip_cm) != 0:
                centered_mm = f"{self.precip_cm}mm"
                precip_text = text(centered_mm, "white", poppins("semi bold"), 30, rf_widget) 
            else:
                centered_mm = f"{self.precip_cm}mm"
                precip_text = text(centered_mm, "white", poppins("semi bold"), 30, rf_widget)
            
            precip_text.setAlignment(Qt.AlignCenter)
        else:
            if (self.precip_inch) == 0:
                precip_text = text(str(0)+'"', "white", poppins("semi bold"), 40, rf_widget, 30)
            else:
                centered_inch = f'{round(self.precip_inch, 1)}"'
                precip_text = text(centered_inch, "white", poppins("semi bold"), 40, rf_widget, 30)
            
            precip_text.setAlignment(Qt.AlignCenter)
        
        
        rf_layout.addWidget(precip_text)
        rf_layout.addStretch(1)
        rf_desc = text("In the next 24 HRS", "white", poppins("semi bold"), 12, rf_widget, -15)
        rf_desc.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        rf_layout.addWidget(rf_desc, alignment=Qt.AlignCenter)
        rf_layout.addStretch(1)
        
        
        # Feels like Column
        
        feels_widget = QWidget()
        feels_layout = QVBoxLayout(feels_widget)
        feels_layout.setContentsMargins(0,0,0,0)
        feels_layout.setSpacing(0)
        
        # Icon & Title (Feels Like)
        
        iwt = QWidget()
        #iwt.setStyleSheet("padding-right: 15px;")
        iwt_layout = QHBoxLayout(iwt)
        iwt_layout.setContentsMargins(0,0,0,0)
        iwt_layout.setSpacing(0)
        iwt_layout.addWidget(svg("./Icons/thermometer.svg", 36, 36))
        feels_index_title = text("Feels like", "white", poppins("semi bold"), 15, iwt)
        feels_index_title.setStyleSheet("color: rgba(255, 255, 255, 0.5); padding-top: 5px; padding-left: 0px; margin-left: 0px;")
        iwt_layout.addWidget(feels_index_title)
        
        # -------------------------
        
        feels_layout.addWidget(iwt, alignment=Qt.AlignCenter)
        
        feels_layout.addStretch(1)

        unit = load_settings()
        is_fahrenheit = unit['units']['temperature'] == "F"

        feels_like = self.feels_like if is_fahrenheit else round((self.feels_like-32)*5/9)
        feels_like_temp = f"{feels_like}\u00b0"
        feels_like_temp = text(feels_like_temp, "white", poppins("semi bold"), 40, feels_widget, 20)
        feels_like_temp.setAlignment(Qt.AlignCenter)
        feels_layout.addWidget(feels_like_temp)
        
        feels_layout.addStretch(1)
        
        if self.feels_like == int(self.current_temp):
            comparison = " Similar"
        elif self.feels_like < int(self.current_temp):
            comparison = "Cooler"
        elif self.feels_like > int(self.current_temp):
            comparison = "Hotter"
        else:
            comparison = " "
            
        comparison = text(comparison, "white", poppins("semi bold"), 13, feels_widget, 0)
        comparison.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        
        feels_layout.addWidget(comparison, alignment=Qt.AlignCenter)
        
        feels_layout.addStretch(1)
        
        column_layout.addWidget(uv_widget, 1)
        column_layout.addSpacing(10)
        column_layout.addWidget(rf_widget, 1)
        column_layout.addSpacing(10)
        column_layout.addWidget(feels_widget, 1)
        
        
        self.uvf_layout.addWidget(column_widget)

    def humidity_air_sun(self):
        self.has = Card(self.viewport, self.element, 250, rain_effect=True if "rain" in self.current_condition.lower() else False)
        self.has.setContentsMargins(105,20,55,0)
        self.has_layout = QVBoxLayout(self.has)
        self.has_layout.setSpacing(0)
        self.populate_has()
    
    def populate_has(self):
        column_widget = QWidget()
        column_layout = QHBoxLayout(column_widget)
        column_layout.setContentsMargins(0,0,0,0)

        # I am copying uvf so i can just add has. I am not gonna change the var names as its a hassle

        uv_widget = QWidget()
        uv_layout = QVBoxLayout(uv_widget)
        uv_layout.setContentsMargins(0,0,0,0)
        uv_layout.setSpacing(4)
        
        # Icon & Title (UV)
        
        iwt = QWidget()
        iwt_layout = QHBoxLayout(iwt)
        iwt_layout.setContentsMargins(0,0,0,0)
        iwt_layout.setSpacing(0)
        iwt_layout.addWidget(svg("./Icons/air-quality.svg", 38, 38))
        uv_index_title = text("Air Quality", "white", poppins("semi bold"), 15, iwt)
        uv_index_title.setStyleSheet("color: rgba(255, 255, 255, 0.5); padding-top: 5px;")
        iwt_layout.addWidget(uv_index_title)
        
        # ====================
        
        
        uv_layout.addWidget(iwt, alignment=Qt.AlignCenter)
        uv_layout.addStretch(1)
        uv_layout.addWidget(text(str(round(int(self.aqi_index))), "white", poppins("semi bold"), 40, uv_widget), alignment=Qt.AlignCenter)
        uv_layout.addStretch(1)

        if self.aqi_index == 1:
            uv_desc = text("Good", "white", poppins("semi bold"), 12, uv_widget)
        elif self.aqi_index == 2:
            uv_desc = text("Fair", "white", poppins("semi bold"), 12, uv_widget)
        elif self.aqi_index == 3:
            uv_desc = text("Moderate", "white", poppins("semi bold"), 12, uv_widget)
        elif self.aqi_index == 4:
            uv_desc = text("Poor", "white", poppins("semi bold"), 12, uv_widget)
        elif self.aqi_index > 4:
            uv_desc = text("Very Poor", "white", poppins("semi bold"), 12, uv_widget)
        
        uv_desc.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        uv_layout.addWidget(uv_desc, alignment=Qt.AlignCenter)
        uv_layout.addSpacing(20)
        
        
        # Rainfall Column
        rf_widget = QWidget()
        rf_layout = QVBoxLayout(rf_widget)
        rf_layout.setContentsMargins(0,0,0,0)
        rf_layout.setSpacing(4)

        # Icon & Title (Rainfall)
                
        rfw = QWidget()
        rfw_layout = QHBoxLayout(rfw)
        rfw_layout.setContentsMargins(0,0,0,0)
        rfw_layout.setSpacing(0)
        rfw_layout.addWidget(svg("./Icons/humidity.svg", 38, 38))
        rf_index_title = text("Humidity", "white", poppins("semi bold"), 15, rfw)
        rf_index_title.setStyleSheet("color: rgba(255, 255, 255, 0.5); padding-top: 5px;")
        rfw_layout.addWidget(rf_index_title)

        # ====================

        rf_layout.addWidget(rfw, alignment=Qt.AlignCenter)
        rf_layout.addStretch(1)

        h_d = QWidget()
        h_d_layout = QVBoxLayout(h_d)
        h_d_layout.setContentsMargins(0,0,0,0)
        h_d_layout.setSpacing(3)

        humidity_string = f"{self.humidity}%"
        precip_text = text(humidity_string, "white", poppins("semi bold"), 40, h_d, 30)
        precip_text.setFixedHeight(50)
        h_d_layout.addWidget(precip_text, alignment=Qt.AlignCenter)

        dew_string = f"Dew Point at {self.dew_point}\u00b0"
        self.dew_point_text = text(dew_string, "white", poppins("semi bold"), 10, h_d, 30)
        self.dew_point_text.setStyleSheet(self.dew_point_text.styleSheet() + "; color: rgba(255, 255, 255, 0.7);")
        h_d_layout.addWidget(self.dew_point_text, alignment=Qt.AlignCenter)

        rf_layout.addWidget(h_d, alignment=Qt.AlignCenter)

        rf_layout.addStretch(1)

        if self.humidity <= 15:
            humidity_rating = "Unhealthy"
        elif self.humidity <= 29:
            humidity_rating = "Fair"
        elif self.humidity <= 50:
            humidity_rating = "Excellent"
        elif self.humidity < 70:
            humidity_rating = "Good"
        else:
            humidity_rating = "Okay"


        rf_desc = text(humidity_rating, "white", poppins("semi bold"), 12, rf_widget, -15)
        rf_desc.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        rf_layout.addWidget(rf_desc, alignment=Qt.AlignCenter)
        rf_layout.addSpacing(20)
        
        
        # Feels like Column
        
        feels_widget = QWidget()
        feels_layout = QVBoxLayout(feels_widget)
        feels_layout.setContentsMargins(0,0,0,0)
        feels_layout.setSpacing(0)
        
        # Icon & Title (Feels Like)
        
        iwt = QWidget()
        #iwt.setStyleSheet("padding-right: 15px;")
        iwt_layout = QHBoxLayout(iwt)
        iwt_layout.setContentsMargins(0,0,0,0)
        iwt_layout.setSpacing(0)
        iwt_layout.addWidget(svg("./Icons/clear-day.svg", 36, 36))
        feels_index_title = text("Daylight", "white", poppins("semi bold"), 15, iwt)
        feels_index_title.setStyleSheet("color: rgba(255, 255, 255, 0.5); padding-top: 5px; padding-left: 0px; margin-left: 0px;")
        iwt_layout.addWidget(feels_index_title)
        
        # -------------------------
        
        feels_layout.addWidget(iwt, alignment=Qt.AlignCenter)
        
        feels_layout.addStretch(1)

        unit = load_settings()
        is_fahrenheit = unit['units']['temperature'] == "F"

        sunrise = QWidget()
        sunrise_layout = QHBoxLayout(sunrise)
        sunrise_layout.setContentsMargins(0,0,0,0)
        sunrise_layout.setSpacing(8)
        sunrise_layout.setAlignment(Qt.AlignCenter)

        sunrise_icon = svg("./Icons/sunrise.svg", 60, 60, reverse=True)
        sunrise_layout.addWidget(sunrise_icon, alignment=Qt.AlignVCenter)

        sunrise_time = text(str(self.sunrise), "white", poppins("semi bold"), 20, sunrise)
        sunrise_time.setStyleSheet(sunrise_time.styleSheet() + "; padding-top: 8px;")
        sunrise_layout.addWidget(sunrise_time, alignment=Qt.AlignVCenter)

        sunset = QWidget()
        sunset_layout = QHBoxLayout(sunset)
        sunset_layout.setContentsMargins(0,0,0,0)
        sunset_layout.setSpacing(8)

        sunset_icon = svg("./Icons/sunset.svg", 60, 60, reverse=True)
        sunset_layout.addWidget(sunset_icon, alignment=Qt.AlignVCenter)

        sunset_time = text(str(self.sunset), "white", poppins("semi bold"), 20, sunset)
        sunset_time.setStyleSheet(sunset_time.styleSheet() + "; padding-top: 8px;")
        sunset_layout.addWidget(sunset_time, alignment=Qt.AlignVCenter)

        feels_layout.addStretch()
        feels_layout.addWidget(sunrise, alignment=Qt.AlignCenter)
        feels_layout.addWidget(sunset, alignment=Qt.AlignCenter)
        feels_layout.addStretch()

        feels_layout.addSpacing(50)


        uv_widget.setMinimumHeight(200)
        rf_widget.setMinimumHeight(200)
        feels_widget.setMinimumHeight(200)
        
        column_layout.addWidget(uv_widget, 1)
        column_layout.addSpacing(10)
        column_layout.addWidget(rf_widget, 1)
        column_layout.addSpacing(10)
        column_layout.addWidget(feels_widget, 1)
        
        
        self.has_layout.addWidget(column_widget)

        
        
        
    def status_bar(self):
        if not hasattr(self, 'status_layout') or self.status_layout is None or sip.isdeleted(self.status_layout):
            self.status = QWidget(self.viewport)
            self.status.setGeometry(35, 75, 828, 120)
            self.status_layout = QHBoxLayout(self.status)
            self.status_layout.setContentsMargins(20, 0, 35, 0)
            self.status_layout.setSpacing(15)
        else:
            while self.status_layout.count():
                child = self.status_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    while child.layout().count():
                        sub = child.layout().takeAt(0)
                        if sub.widget():
                            sub.widget().deleteLater()
        


        if self.current_weather_id == 800:
            if self.ismorning:
                condition = svg("./Icons/clear-day.svg", 190, 190)
            else:
                condition = svg("./Icons/clear-night.svg", 190, 190)
        elif self.current_weather_id == 804:
            condition = svg("./Icons/cloudy.svg", 190, 190)
        elif self.current_weather_id in (801, 802, 803):
            if self.ismorning:
                condition = svg("./Icons/partly-cloudy-day.svg", 190, 190)
            else:
                condition = svg("./Icons/partly-cloudy-night.svg", 190, 190)
        elif self.current_weather_id in (500, 501, 502, 503, 504, 520, 521, 522, 531):
            if self.current_weather_id == 500:
                condition = svg("./Icons/drizzle.svg", 190, 190)
            else:
                condition = svg("./Icons/rain.svg", 190, 190)
        elif self.current_weather_id in (200, 201, 202, 210, 211, 212, 221, 230, 231, 232):
            condition = svg("./Icons/thunderstorm.svg", 190, 190)
        elif self.current_weather_id in (300, 301, 302, 310, 311, 312, 321):
            condition = svg("./Icons/drizzle.svg", 190, 190)
        elif self.current_weather_id in (600, 601, 602, 611, 612, 615, 616, 620, 621, 621):
            condition = svg("./Icons/snowflake.svg", 190, 190)
        elif self.current_weather_id == 611:
            condition = svg("./Icons/hail.svg", 190, 190)
        elif self.current_weather_id == 721:
            condition = svg("./Icons/haze.svg", 190, 190)
        elif self.current_weather_id == 731:
            condition = svg("./Icons/dust.svg", 190, 190)
        elif self.current_weather_id in (701, 741):
            condition = svg("./Icons/fog.svg", 190, 190)
        else:
            print(f"No icon for {self.current_weather_id}")
        
        


        #condition.setStyleSheet("margin-top: 22px;")

        unit = load_settings()
        is_fahrenheit = unit['units']['temperature'] == "F"

        temp_number = self.raw_temp
        temp_c = str(round(((int(temp_number)-32)*5/9)))

        if is_fahrenheit:
            temp = text(str(temp_number)+"\u00b0", "white", poppins("semi bold"), 65, self.status)
        else:
            temp = text(str(temp_c)+"\u00b0", "white", poppins("semi bold"), 65, self.status)
        
        temp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        temp.setContentsMargins(0, 25, 0, 0)
        temp.setMinimumWidth(200)

        
        self.status_layout.addWidget(condition, alignment=Qt.AlignTop)
        self.status_layout.addWidget(temp)


        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_layout.setSpacing(5)
        
        self.condition = text(self.current_condition, "white", poppins("semi bold"), 45, self.status)

        if len(self.condition.text()) > 10:
            self.condition.deleteLater()
            self.condition = text(self.current_condition, "white", poppins("semi bold"), 35, self.status)

        
        self.condition.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.condition.setMaximumHeight(70)

        if "clouds" in str(self.current_condition).lower():
            self.condition.setText("Cloudy")
        
        
        if self.initial_place:
            location = text(str(self.current_location_name), "white", poppins("semi bold"), 20, self.status)
        else:
            if len(str(self.current_location_name)) < 18:
                location = text(str(self.current_location_name), "white", poppins("semi bold"), 20, self.status)
            else:
                location = text(str(self.current_location_name)[:14]+"...", "white", poppins("semi bold"), 20, self.status)
            

        location.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        location.setMaximumHeight(30)
        location.setStyleSheet(location.styleSheet() + "; margin-right: 1px;")

        info_layout.addWidget(location)
        info_layout.addWidget(self.condition)
        
        self.status_layout.addLayout(info_layout)

        self.status.show()
        self.condition.show()
        temp.show()
        location.show()

    
    def open_credits(self, event):
        file = "./attribution.txt"
        current_os = platform.system()

        def check(internet_check):
            if internet_check:
                chrome = webbrowser.get('C:/Program Files/Google/Chrome/Application/chrome.exe %s')
                try: chrome.open_new_tab("https://github.com/sri497111/Skyline/blob/main/attribution.txt") 
                except: chrome.open_new("https://github.com/sri497111/Skyline/blob/main/attribution.txt")
            else:
                try: 
                    if current_os == "Windows":
                        os.startfile(os.path.abspath(file))
                    elif current_os == "Darwin":
                        subprocess.run(['open', os.path.abspath(file)])
                    else:
                        webbrowser.open(os.path.abspath(file))
                except:
                    print("Error")
        internet_check(callback=check)

    def closeEvent(self, event):
        edit_html(reverse=True)
        event.accept()
                    

        
def main():

    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--js-flags='--expose-gc' "
        "--aggressive-cache-discard "
        "--enable-aggressive-domstorage-flushing"
    )
    
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon("./skyline.ico"))
    
    window = MainWindow()
    
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
