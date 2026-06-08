# Qt Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QPushButton, QVBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontDatabase, QPixmap
from PyQt5 import QtWidgets
from PyQt5.QtSvg import QSvgWidget

# Modules
from location import *
from retrieve import Weather
from ui_engine import Card, text, button, poppins

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
        
        self.windowsize = (SIZE[0], SIZE[1])
        self.refresh_rate = get_refresh_rate()
        self.frequency = int(round(1000/self.refresh_rate, 0))
        
        self.friction = 0.92
        self.sensitvity = 0.03
        self.yv = 0
        self.v = 0
        
        self.setStyleSheet("""
            QMainWindow {
                border-image: url('./Backgrounds/cloudy/blurclouds.png') 0 0 0 0 stretch stretch;
            }
        """)
        
        
        self.element = QPixmap("./Backgrounds/cloudy/elementblur.png")
        
        
        widget = QWidget()
        self.viewport = QWidget(widget)
        self.viewport.setGeometry(0, 0, 878, 1000)
        
        self.hourly_forecast = Card(self.viewport, self.element, 200)
        self.daily_forecast = Card(self.viewport, self.element, 500)
        self.daily_forecast.setContentsMargins(35,0,0,0)
        
        condition = text("Cloudy", "white", poppins("semi bold"), 50, self.viewport)
        condition.setContentsMargins(35, 0, 0, 0)
        
        main_layout = QVBoxLayout(self.viewport)
        main_layout.setContentsMargins(25, 75, 25, 25)
        main_layout.setSpacing(30)
        
        main_layout.addWidget(condition)
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
        
            
def main():   
    app = QApplication(sys.argv)
    
    window = MainWindow()
    
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
