# Qt Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QPushButton, QVBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase, QPixmap
from PyQt5 import QtWidgets
from PyQt5.QtSvg import QSvgWidget

# Modules
from location import *
from retrieve import Weather
from ui_engine import Card, text, button, poppins

# System
import sys
import datetime

# --------------------------------------------------------------------------


SIZE = (878, 550)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(SIZE[0], SIZE[1])
        self.windowsize = (SIZE[0], SIZE[1])
        self.setStyleSheet("""
            QMainWindow {
                border-image: url('./Backgrounds/cloudy/clouds.png') 0 0 0 0 stretch stretch;
            }
        """)
        
        self.element = QPixmap("./Backgrounds/cloudy/elementblur.png")
        
        
        
        widget = QWidget()
        
        hourly_forecast = Card(widget, self.element, 200)
        daily_forecast = Card(widget, self.element, 500)
        daily_forecast.setContentsMargins(35,0,0,0)
        
        condition = text("Cloudy", "white", poppins("semi bold"), 50, widget)
        condition.setContentsMargins(35, 0, 0, 0)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 75, 25, 25)
        main_layout.setSpacing(30)
        
        main_layout.addWidget(condition)
        main_layout.addWidget(hourly_forecast)
        main_layout.addSpacing(150)
        main_layout.addWidget(daily_forecast)
        
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)
        
        
def main():   
    app = QApplication(sys.argv)
    
    window = MainWindow()
    
    
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()