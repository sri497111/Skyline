# Qt Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QSpacerItem, QSizePolicy, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QEasingCurve, QEventLoop, QEvent, QParallelAnimationGroup, QPoint
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import QGraphicsBlurEffect, QGraphicsOpacityEffect, QFrame
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtGui import QPixmap, QPainterPath, QRegion, QFont
from PyQt5 import sip

# Modules
from ui_engine import Card, text, Button, poppins, svg, hover_svg, Loading_Icon, Popup, RadioButton, mouse_press_dim, mouse_release_dim, hover_text, WeatherCard
from retrieve import Weather, WeatherWait, DashboardWeather, DashboardWeatherWait, parse_hourly_forecast, parse_daily_forecast, parse_forecast_for_precip, edit_html
from settings import load_settings, update_settings, check_theme
from system import internet_check
from location import *

# System
from system import *
import webbrowser
import subprocess
import platform
import datetime
import sys
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
        
        self.network = QNetworkAccessManager()

        self.first_load = True

        self.popup_active = False

        self.initial_place = True

        self.add_coords = None
        
        # Init Weather
        self.location = (29.4243, -98.4911)

        self.dash_weather = []

        self.centralwidget = QWidget()
        self.setCentralWidget(self.centralwidget)

        # Init Viewport and screening (content)

        self.viewport = QWidget(self.centralwidget)
        self.viewport.setGeometry(0, 0, 878, 1800)
        self.viewport.setStyleSheet("background: transparent; border: none; border-radius: 0px;")
        

        self.ui_blur = QGraphicsBlurEffect()
        self.ui_blur.setBlurRadius(40)
        self.ui_blur.setBlurHints(QGraphicsBlurEffect.QualityHint)
        self.viewport.setGraphicsEffect(self.ui_blur)
        

        self.loading = Loading_Icon("./Icons/loading.svg", 64 )
        self.loading.setParent(self.centralwidget)
        self.loading.move((self.width()-self.loading.width())//2, (self.height()-self.loading.height())//2)
        self.loading.show()
        self.loading.raise_()

        self.wait = WeatherWait(self.location)
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
        
        
    def loaded(self, data):    
        
        self.fade = QGraphicsOpacityEffect(self.viewport)
        self.fade.setOpacity(0.0)
        self.viewport.setGraphicsEffect(self.fade)


        self.current_weather = data['current']

        self.current_weather_data = self.current_weather
        
        self.current_location_name = str(self.current_weather_data["name"])
        
        self.current_temp = str(round(int(self.current_weather_data['main']['temp']), 0))
        self.raw_temp = round(int(self.current_weather_data['main']['temp']), 0)
        self.current_condition = str(self.current_weather_data["weather"][0]["main"])
        
        self.weather_forecast_data = data['forecast']
        self.weather_hourly_forecast_data = parse_hourly_forecast(self.weather_forecast_data, increment=5)
        
        self.weather_daily_forecast_data = parse_daily_forecast(self.weather_forecast_data)
        
        self.feels_like = round(int(self.current_weather_data['main']['feels_like']))
        
        self.precip_inch = parse_forecast_for_precip(self.weather_forecast_data)[0]
        self.precip_cm = parse_forecast_for_precip(self.weather_forecast_data)[1]
        
        self.uv_index = data['uv']

        self.map_pixmap = data['map']
        
        # Init Widgets

        self.menu_bar()
        self.status_bar()
        self.hourly()
        self.daily()
        self.uv_and_feels_like()
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

        main_layout.addWidget(self.uvf)

        main_layout.addSpacing(30)
        
        main_layout.addWidget(self.weather_map_card)

        self.viewport.setLayout(main_layout)

        QApplication.processEvents()

        self.menu_card.updatePixmap()
        self.hourly_forecast.updatePixmap()
        self.daily_forecast.updatePixmap()
        self.uvf.updatePixmap()
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
        self.fade_out.setDuration(200)
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
        self.fade_out.start()

        self.fade_in = QPropertyAnimation(self.fade, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        
        self.fade_in.finished.connect(lambda: self.viewport.setGraphicsEffect(None))
        self.fade_in.start()


    def error(self, msg):
        print("Error -                {msg}")
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
                condition = weather_list[0].get("main", "N/A") if weather_list else "N/A"
                
                main_data = current_info.get("main", {})
                current_temp = str(int(round(main_data.get("temp", 0))))

                daily_min_list = hi_lo_info.get("daily", {}).get('temperature_2m_min', [])
                daily_max_list = hi_lo_info.get("daily", {}).get('temperature_2m_max', [])

                hi = str(int(round(daily_max_list[0]))) if daily_max_list else "N/A"
                low = str(int(round(daily_min_list[0]))) if daily_min_list else "N/A"

                self.dash_weather.append([location_name, condition, current_temp, hi, low])




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
                elif self.yv < -1250:
                    self.yv = -1250
                    self.v = 0
                


                self.sensitvity = 0.03
                self.viewport.move(0, int(self.yv))

                self.menu_card.updatePixmap()
                self.hourly_forecast.updatePixmap()
                self.daily_forecast.updatePixmap()
                self.uvf.updatePixmap()
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

            self.suggestions = Card(self.searchpop, self.element, 400, raise_dark=False)

            self.suggestions.dark.setStyleSheet(f"""
                background: rgba(0,0,0,50);
                border-radius: {55}px;
            """)

            if theme == 0:
                self.suggestions.dark.setStyleSheet(f"""
                    background: rgba(0,0,0,50);
                    border-radius: {35}px;
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
                    btn.mousePressEvent = lambda event, c=coords: self.change_location(event, c)
                else:
                    def select_location(event, c=coords):
                        self.add_coords = c

                        if hasattr(self, 'searchpop') and self.searchpop:
                            self.searchpop.exit_popup()

                        self.add_card(event)
                    
                    

                    btn.mousePressEvent = lambda event, c=coords: select_location(event, c)

                self.suggestions_layout.setAlignment(Qt.AlignTop)
                self.suggestions_layout.addWidget(btn)

        else:
            no_results = text("No results found.", "white", poppins("semi bold"), 14, parent=self.suggestions, transparency=True)
            self.suggestions_layout.addWidget(no_results, alignment=Qt.AlignCenter)

        QApplication.processEvents()
        QTimer.singleShot(50, self.suggestions.updatePixmap)

    def change_location(self, event, coords):
        if hasattr(self, 'searchpop') and self.searchpop:
            self.searchpop.exit_popup()

        hide_viewport = QGraphicsOpacityEffect()
        hide_viewport.setOpacity(0.0)

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

            self.settings_card = Card(self.settingspop, self.element, 400, raise_dark=False)
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
            self.weather_map_card,
        ]

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
                        border-radius: 30px;                      
                ''')
                if getattr(self, 'temp_radio', None): self.temp_radio.radio_card.dark.setStyleSheet("background: rgba(0,0,0,70); border-radius: 35px;")
                if getattr(self, 'theme_radio', None): self.theme_radio.radio_card.dark.setStyleSheet("background: rgba(0,0,0,70); border-radius: 35px;")
                if getattr(self, 'length_radio', None): self.length_radio.radio_card.dark.setStyleSheet("background: rgba(0,0,0,70); border-radius: 35px;")
                if getattr(self, 'credits', None): self.credits.dark.setStyleSheet("background: rgba(0,0,0,70); border-radius: 35px;")
            
            else:
                self.settings_card.dark.setStyleSheet('''
                        background: rgba(255,255,255,10);
                        border-radius: 30px;                      
                ''')

                if getattr(self, 'temp_radio', None): self.temp_radio.radio_card.dark.setStyleSheet("background: rgba(255,255,255,30); border-radius: 35px;")
                if getattr(self, 'theme_radio', None): self.theme_radio.radio_card.dark.setStyleSheet("background: rgba(255,255,255,30); border-radius: 35px;")
                if getattr(self, 'length_radio', None): self.length_radio.radio_card.dark.setStyleSheet("background: rgba(255,255,255,30); border-radius: 35px;")
                if getattr(self, 'credits', None): self.credits.dark.setStyleSheet("background: rgba(255,255,255,30); border-radius: 35px;")

            self.settings_card.updatePixmap()
            if getattr(self, 'temp_radio', None): self.temp_radio.radio_card.updatePixmap()
            if getattr(self, 'theme_radio', None): self.theme_radio.radio_card.updatePixmap()
            if getattr(self, 'length_radio', None): self.length_radio.radio_card.updatePixmap()
            if getattr(self, 'credits', None): self.credits.updatePixmap()
        
        QApplication.processEvents()

    def unit_change(self, index=None):
        QTimer.singleShot(0, self.apply_unit_change)

    def apply_unit_change(self):
        global LENGTH_UNIT, SPEED_UNIT

        unit = load_settings()
        LENGTH_UNIT = unit['units']['length']
        SPEED_UNIT = unit['units']['speed']

        self.status_bar()

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

        QApplication.processEvents()
        if hasattr(self, 'hourly_forecast'): self.hourly_forecast.updatePixmap()
        if hasattr(self, 'daily_forecast'): self.daily_forecast.updatePixmap()
        if hasattr(self, 'uvf'): self.uvf.updatePixmap()


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
                        hi = self.dash_weather[idx-1][3]
                        low = self.dash_weather[idx-1][4]
                    else:
                        current_weather = "..."
                        current_temp = "--"
                        hi = "--"
                        low = "--"

                    card = WeatherCard(self.dashboard_container, opaque_element, location_name=loc_name, current_condition=current_weather, current_temp=current_temp, hi=hi, low=low)

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
                conditon = weather_list[0].get("main", "N/A")
            else:
                conditon = "N/A"

            main_data = current_info.get("main", {})
            temp = main_data.get("temp", "N/A") if isinstance(main_data, dict) else "N/A"

            daily_max = hi_lo_info.get("daily", {}).get('temperature_2m_max', 0)
            daily_min = hi_lo_info.get("daily", {}).get('temperature_2m_min', 0)

            temp_max = round(daily_max[0]) if daily_max else "N/A"
            temp_min = round(daily_min[0]) if daily_min else "N/A"
            current_temp = round(temp) if isinstance(temp, (int,float)) else "N/A"

            if hasattr(card, "condition_label"):
                card.condition_label.setText(str(conditon))
            if hasattr(card, "temp_label"):
                card.temp_label.setText(f"{current_temp}\u00b0")
            if hasattr(card, 'hi_lo_label'):
                card.hi_lo_label.setText(f"H: {temp_max}\u00b0 L: {temp_min}\u00b0")
 
            daily_min_list = hi_lo_info.get("daily", {}).get('temperature_2m_min', [])
            daily_max_list = hi_lo_info.get("daily", {}).get('temperature_2m_max', [])

            hi = str(int(daily_max_list[0])) if daily_max_list else "N/A"
            low = str(int(daily_min_list[0])) if daily_min_list else "N/A"

            self.dash_weather.append([conditon, temp, hi, low])
            
        
        
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

            if hasattr(self, 'results') and self.results:
                location = self.results[0][0]

            card = WeatherCard(self.dashboard_container, opaque_element, location, lat, lon)
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

            if len(self.dash_cards) < 5 and hasattr(self, 'add_card_btn') and self.add_card and not sip.isdeleted(self.add_card_btn):
                self.dashboard_layout.addWidget(self.add_card_btn, alignment=Qt.AlignCenter)
            elif len(self.dash_cards) >= 5 and hasattr(self, 'add_card_btn') and self.add_card and not sip.isdeleted(self.add_card_btn):
                self.add_card_btn.hide()

            self.save_dashboard()
            self.refresh_dashboard_data()

    def check_add_btn(self):
        if hasattr(self, 'add_card_btn') and self.add_card_btn and not sip.isdeleted(self.add_card_btn):
            if len(self.dash_cards) < 5:
                self.add_card_btn.show()
                self.add_card_btn.raise_()
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

        if hasattr(self, 'add_card_btn') and self.add_card and not sip.isdeleted(self.add_card_btn):
            self.dashboard_layout.addWidget(self.add_card_btn, alignment=Qt.AlignCenter)

        self.check_add_btn()

    def card_drag_press(self, event, card):
        if event.button() == Qt.LeftButton:
            card.dragging = True
            card.drag_start_pos = event.globalPos()
            card.original_y = card.y()
            card.original_x = card.x()
            card.swipe = False
            card.vertical_swipe = False

            card.raise_()
            card.setCursor(Qt.ClosedHandCursor)

    def card_drag_move(self, event, card):
        if not hasattr(card, 'drag_global_start_x'):
            card.drag_global_start_x = event.globalX()
            card.drag_global_start_y = event.globalY()
        
        delta = event.globalPos() - card.drag_start_pos
        dx = delta.x()
        dy = delta.y()

        
        if not getattr(card, 'swipe', False) and not getattr(card, 'vertical_swipe', False):
            if abs(dx) > 30 or abs(dx) > abs(dy):
                if abs(dx) > 30 and abs(dx) > abs(dy):
                    card.swipe = True
                else:
                    card.vertical_swipe = True
                    
        if getattr(card, 'swipe', False):
            if card.parent() != self:
                window_position = self.mapFromGlobal(card.mapToGlobal(QPoint(0,0)))
                
                card.placeholder = QWidget()
                card.placeholder.setFixedSize(card.width(), card.height())
                card.placeholder.setStyleSheet("background: transparent;")
                self.dashboard_layout.insertWidget(self.dashboard_layout.indexOf(card), card.placeholder, alignment=Qt.AlignCenter)
                
                card.setParent(self)
                card.move(window_position)
                card.show()
                card.raise_()
                card.drag_start_x = window_position.x()
                card.drag_start_y = window_position.y()

            
            new_x = card.drag_start_x + dx
            card.move(int(new_x), card.original_y)
            return
        

        if getattr(card, 'vertical_swipe', False):
            if card.parent() != self:
                window_position = self.mapFromGlobal(card.mapToGlobal(QPoint(0,0)))
                
                card.placeholder = QWidget()
                card.placeholder.setFixedSize(card.width(), card.height())
                card.placeholder.setStyleSheet("background: transparent;")


                self.dashboard_layout.insertWidget(self.dashboard_layout.indexOf(card), card.placeholder, alignment=Qt.AlignCenter)
                
                card.setParent(self)
                card.move(window_position)
                card.show()
                card.raise_()
                card.drag_start_x = window_position.x()
                card.drag_start_y = window_position.y()
            
            new_y = card.drag_start_y + dy
            card.move(card.x(), new_y)

            current = self.dash_cards.index(card)
            card.index = current
            spacing = self.dashboard_layout.spacing() if self.dashboard_layout.spacing() >= 0 else 15
            rowh = card.height()+spacing
            top_margin = 50
            target_y = (current * rowh) + top_margin

            if current > 0 and new_y < target_y - (rowh/2):
                # Kinda like a neighbor checking
                nextto = self.dash_cards[current-1]
                self.dash_cards[current], self.dash_cards[current - 1] = nextto, card
                card.index -= 1
                nextto.index += 1
                self.glide(nextto, nextto.index * rowh + top_margin)
            
            elif current < len(self.dash_cards) - 1 and new_y > target_y + (rowh / 2):
                nextto = self.dash_cards[current + 1]
                self.dash_cards[current], self.dash_cards[current+1] = nextto, card
                card.index += 1
                nextto.index -= 1
                self.glide(nextto, (nextto.index * rowh) + top_margin)

            return
        


    def card_drag_release(self, event, card):
        if not card.dragging:
            return
        
        card.dragging = False
        card.setCursor(Qt.OpenHandCursor)

        if getattr(card, 'swipe', False):
            card.swipe = False
            delta_x = card.x() - getattr(card, 'drag_start_x', getattr(card, 'original_x', 0))

            if delta_x > 140:
                self.dismiss_card(card)
            else:
                if hasattr(card, 'placeholder') and card.placeholder:
                    self.dashboard_layout.removeWidget(card.placeholder)
                    card.placeholder.deleteLater()
                    card.placeholder = None

                target_y = (card.index * (card.height()+15)) + 50
                card.setParent(self.dashboard_container)
                card.show()
                card.move(getattr(card, 'original_x', 0), target_y)
                self.rebuild_dash()
            return

        card.vertical_swipe = False

        self.rebuild_dash()

        rowh = card.height() + 15
        target_y = (card.index * rowh) + 50
        self.glide(card, target_y)

        card.updatePixmap()
        self.save_dashboard()

    def dismiss_card(self, card):
        init_pos = card.pos()

        end_x = self.width()+100
        end_pos = QPoint(end_x, init_pos.y())

        card.anim = QPropertyAnimation(card, b'pos')
        card.anim.setDuration(250)
        card.anim.setStartValue(init_pos)
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

            if hasattr(self, 'add_card_btn') and self.add_card and not sip.isdeleted(self.add_card_btn):
                add_btn_target = (len(self.dash_cards) * rowh) + 50
                self.glide(self.add_card_btn, add_btn_target)

            QTimer.singleShot(225, self.check_add_btn)
            self.save_dashboard()

        card.anim.finished.connect(slide_finished)
        card.anim.start()

    
    def glide(self, card, target_y):
        if hasattr(card, 'anim') and card.anim is not None:
            card.anim.stop()
        
        card.anim = QPropertyAnimation(card, b'pos')
        card.anim.setDuration(250)
        card.anim.setEndValue(QPoint(card.x(),  int(target_y)))
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

        unit = load_settings()
        is_fahrenheit = unit['units']['temperature'] == "F"
        is_mph = unit['units']['speed'] == "MPH"
        
        for i in range(5):
            horizontal_widget = QWidget()
            horizontal_widget.setFixedHeight(90)
            
            hbox = QHBoxLayout(horizontal_widget)
            hbox.setContentsMargins(5,0,0,0)
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
            cond.setFixedWidth(64)
            hbox.addWidget(cond)
            
            day = data[i][0]
            day = text(day, "white", poppins("semi bold"), 20, horizontal_widget)
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
        self.weather_map_card = Card(self.viewport, self.element, 350)
        self.weather_map_card.setCursor(Qt.PointingHandCursor)
        self.weather_map_card.dark.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        
        self.map_layout = QVBoxLayout(self.weather_map_card)
        self.map_layout.setContentsMargins(25,20,25,20)
        self.map_layout.setAlignment(Qt.AlignCenter)
        
        self.map_label = QLabel()
        
        pixmap = self.map_pixmap.scaled(778, 305, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.map_label.setPixmap(pixmap)
        self.map_label.setFixedSize(778, 305)
        self.map_label.setScaledContents(True)
        
        self.click_event = QPushButton(self.map_label)
        self.click_event.setStyleSheet("background-color: transparent; border: none;")
        self.click_event.clicked.connect(self.popup)
        
        self.click_event.setGeometry(0,0,778,305)
        
        path = QPainterPath()
        path.addRoundedRect(0,0, 778, 305, 45, 45)
        self.map_label.setMask(QRegion(path.toFillPolygon().toPolygon()))
        
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
        settings = map_widget.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)

        theme = check_theme()

        if theme == 0: self.path = os.path.abspath("./map-dark.html")
        else: self.path = os.path.abspath("./map-dark.html")
        
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
        self.uvf = Card(self.viewport, self.element, 250)
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
        

        if str(self.current_condition).lower() == "clouds":
                condition = svg("./Icons/cloudy.svg", 190, 190)
        elif str(self.current_condition).lower() == "clear":
            condition = svg("./Icons/clear-day.svg", 190, 190)
        elif str(self.current_condition).lower() == "rain":
            condition = svg("./Icons/rain.svg", 190, 190)
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
        
        condition = text(self.current_condition, "white", poppins("semi bold"), 45, self.status)
        condition.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        condition.setMaximumHeight(70)
        
        if self.initial_place:
            location = text(str(self.current_location_name), "white", poppins("semi bold"), 20, self.status)
        elif len(self.results[0][0]) < 20:
            location = text(str(self.results[0][0]), "white", poppins("semi bold"), 20, self.status)
        else:
            if len(str(self.current_location_name)) < 18:
                location = text(str(self.current_location_name), "white", poppins("semi bold"), 20, self.status)
            else:
                location = text(str(self.current_location_name)[:14]+"...", "white", poppins("semi bold"), 20, self.status)
            

        location.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        location.setMaximumHeight(30)
        location.setStyleSheet(location.styleSheet() + "; margin-right: 1px;")

        info_layout.addWidget(location)
        info_layout.addWidget(condition)
        
        self.status_layout.addLayout(info_layout)

        self.status.show()
        condition.show()
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
                    

        
def main():

    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--js-flags='--expose-gc' "
        "--aggressive-cache-discard "
        "--enable-aggressive-domstorage-flushing"
    )
    
    app = QApplication(sys.argv)
    
    window = MainWindow()
    
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()