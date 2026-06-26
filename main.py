# Qt Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QSpacerItem, QSizePolicy, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFontDatabase, QPixmap, QPainterPath, QRegion, QFont
from PyQt5 import QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWidgets import QGraphicsBlurEffect, QGraphicsOpacityEffect
from PyQt5 import sip

# Modules
from location import *
from retrieve import Weather, WeatherWait, parse_hourly_forecast, parse_daily_forecast, parse_forecast_for_precip, edit_html
from ui_engine import Card, text, Button, poppins, svg, hover_svg, Loading_Icon, Popup

# System
from system import *
import sys
import datetime
import os
import gc

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
        
        self.popup_active = False
        
        # Init Weather
        self.location = (29.4243, -98.4911)
        self.weather_vars(self.location)
        

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
        
        
    def loaded(self, data):    
        

        self.current_weather = data['current']

        self.current_weather_data = self.current_weather
        
        self.current_location_name = str(self.current_weather_data["name"])
        
        self.current_temp = str(round(int(self.current_weather_data['main']['temp']), 0))
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

        self.timer = QTimer()
        self.timer.timeout.connect(self.intertia)
        self.timer.start(self.frequency)

        
        
        self.load_fade = QGraphicsOpacityEffect(self.loading)
        self.load_fade.setOpacity(0.0)
        self.loading.setGraphicsEffect(self.load_fade)

        self.fade_out = QPropertyAnimation(self.load_fade, b"opacity")
        self.fade_out.setDuration(200)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        
        self.fade_out.finished.connect(lambda: self.loading.setGraphicsEffect(None))
        self.fade_out.start()

        if self.loading is not None:
            if hasattr(self.loading, "timer"):
                self.loading.timer.stop()
            self.loading.hide()
            self.loading.deleteLater()
            self.loading = None

        self.fade = QGraphicsOpacityEffect(self.viewport)
        self.fade.setOpacity(0.0)
        self.viewport.setGraphicsEffect(self.fade)

        self.fade_in = QPropertyAnimation(self.fade, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        
        self.fade_in.finished.connect(lambda: self.viewport.setGraphicsEffect(None))
        self.fade_in.start()


    def error(self):
        error_label = text("Error retrieving data...", "white", poppins("semi bold"), 20, self.viewport)
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setGeometry(0, 0, self.viewport.width(), self.viewport.height())
        error_label.show()

    def wheelEvent(self, event):
        self.v += event.angleDelta().y() * self.sensitvity
    def intertia(self):
        if self.v > 0.05 or self.v < -0.05:
            self.yv += self.v
            self.v *= self.friction
            
            self.viewport.move(0, int(self.yv))
            
            self.menu_card.updatePixmap()
            self.hourly_forecast.updatePixmap()
            self.daily_forecast.updatePixmap()
            self.uvf.updatePixmap()
            self.weather_map_card.updatePixmap()
            
        else:
            if self.v != 0:
                self.v = 0
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
        search.mousePressEvent = self.search
        self.menu_layout.addWidget(search)

        dashboard = hover_svg("./Icons/places.svg", 30, 30)
        dashboard.setCursor(Qt.PointingHandCursor)
        self.menu_layout.addWidget(dashboard)
        
        settings = hover_svg("./Icons/settings.svg", 30, 30)
        settings.setCursor(Qt.PointingHandCursor)
        self.menu_layout.addWidget(settings)
    
    def search(self, event):
        if not hasattr(self, 'searchpop') or self.searchpop == None:
            self.searchpop = Popup(self)
            self.searchpop.destroyed.connect(lambda: setattr(self, 'searchpop', None))

            self.search_bar = Card(self.searchpop, self.element, 70, radius=35, raise_dark=False) 
            self.search_bar.setFixedWidth(600)
            self.search_bar.dark.setStyleSheet(f"""
                background: rgba(0,0,0,50);
                border-radius: {35}px;
            """)
            search_layout = QHBoxLayout(self.search_bar)
            search_layout.setContentsMargins(40,0,40,0)
            self.location_search = QLineEdit(self.menu_card)
            self.location_search.setPlaceholderText("Search an adress, city or place.")
            self.location_search.setStyleSheet("background: transparent; border: none; color: white; font-size: 18px;")
            self.location_search.setFont(QFont(poppins("semi bold"), 12))
            search_layout.addWidget(self.location_search, alignment=Qt.AlignVCenter)

            self.suggestions = Card(self.searchpop, self.element, 300)
            self.suggestions.dark.setStyleSheet(f"""
                background: rgba(0,0,0,50);
                border-radius: {55}px;
            """)

            suggestions_layout = QVBoxLayout(self.suggestions)
            suggestions_layout.setContentsMargins(40,0,40,0)

            for i in range(5):
                suggestions_layout.addWidget(text("Location", "white", poppins("semi bold"), 24, suggestions_layout), alignment=Qt.AlignLeft)

            self.searchpop.popup_layout.addWidget(self.search_bar, alignment=Qt.AlignCenter)
            self.searchpop.popup_layout.addWidget(self.suggestions)

            QApplication.processEvents()

            self.search_bar.updatePixmap()
            self.suggestions.updatePixmap()


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
            
            min_max = data[i][2], data[i][3]
            min_max_string = f"{min_max[0]}\u00b0 / {min_max[1]}\u00b0"
            min_max = text(min_max_string, "white", poppins("semi bold"), 20, horizontal_widget)
            min_max.setFixedWidth(120)
            min_max.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            if int(data[i][4]) == 0:
                end_icon = svg("./Icons/wind.svg", 51, 51)
                num = text(str(data[i][5])+" "+SPEED_UNIT, "white", poppins("semi bold"), 17, horizontal_widget)
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

        self.path = os.path.abspath("./map-light.html")
        map_widget.setUrl(QUrl.fromLocalFile(self.path))
        map_layout.addWidget(map_widget)
        
        QApplication.processEvents()

        #self.map_fade_effect = QGraphicsOpacityEffect(self.popup_card)
        #self.map_label.setGraphicsEffect(self.map_fade_effect)

        #self.map_fade = QPropertyAnimation(self.map_fade_effect, b'opacity')
        #self.map_fade.setDuration(200)
        #self.map_fade.setStartValue(0.0)
        #self.map_fade.setEndValue(1.0)

        #self.map_fade.setEasingCurve(QEasingCurve.InOutQuad)

        #self.map_fade.finished.connect(lambda: self.popup_card.setGraphicsEffect(None))

        self.popup_card.show()
        self.popup_card.raise_()
        #self.map_fade.start()
        
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
        uv_layout.addWidget(text(str(self.uv_index), "white", poppins("semi bold"), 40, uv_widget), alignment=Qt.AlignCenter)
        uv_layout.addStretch(1)
        uv_desc = text("Moderate", "white", poppins("semi bold"), 12, uv_widget)
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
        
        if LENGTH_UNIT == "MM":
            if int(self.precip_cm) != 0:
                precip_text = text(str(self.precip_cm)+'mm', "white", poppins("semi bold"), 40, rf_widget) 
            else:
                precip_text = text(' '+str(0)+'mm', "white", poppins("semi bold"), 40, rf_widget)
            
        else:
            if int(self.precip_inch) == 0:
                precip_text = text(str(0)+'"', "white", poppins("semi bold"), 40, rf_widget, 30)
            else:
                precip_text = text(str(self.precip_inch)+'"', "white", poppins("semi bold"), 40, rf_widget)
        
        
        rf_layout.addWidget(precip_text, alignment=Qt.AlignCenter)
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
        
        feels_like_temp = text(' '+str(self.feels_like)+"\u00b0", "white", poppins("semi bold"), 40, feels_widget, 20)
        feels_layout.addWidget(feels_like_temp, alignment=Qt.AlignCenter)
        
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
        
    def weather_vars(self, location):
        pass
        
        
        
    def status_bar(self):
        self.status = QWidget(self.viewport)
        self.status.setGeometry(35, 75, 828, 120)
        status_layout = QHBoxLayout(self.status)
        status_layout.setContentsMargins(20, 0, 35, 0)
        status_layout.setSpacing(15)
        

        if str(self.current_condition).lower() == "clouds":
                condition = svg("./Icons/cloudy.svg", 190, 190)
        elif str(self.current_condition).lower() == "clear":
            condition = svg("./Icons/clear-day.svg", 190, 190)
        elif str(self.current_condition).lower() == "rain":
            condition = svg("./Icons/rain.svg", 190, 190)
        #condition.setStyleSheet("margin-top: 22px;")
        
        temp = text(self.current_temp+"\u00b0", "white", poppins("semi bold"), 65, self.status)
        temp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        temp.setContentsMargins(0, 25, 0, 0)
        temp.setMinimumWidth(200)

        
        status_layout.addWidget(condition, alignment=Qt.AlignTop)
        status_layout.addWidget(temp)


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
