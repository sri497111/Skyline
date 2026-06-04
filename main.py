# Qt Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QPushButton, 
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

GLOBAL_DPI_SCALE_POINT = 96.0

def scale(app):
    screen = app.primaryScreen()
    dpi = screen.logicalDotsPerInch()
    return dpi / GLOBAL_DPI_SCALE_POINT


SIZE = (975, 610)


class MainWindow(QMainWindow):
    def __init__(self, scale):
        super().__init__()
        self.scale = scale
        self.setFixedSize(self.s(SIZE[0]), self.s(SIZE[1]))
        self.windowsize = (self.s(SIZE[0]), self.s(SIZE[1]))
        self.setStyleSheet("""
            QMainWindow {
                border-image: url('./Backgrounds/cloudy/clouds.png') 0 0 0 0 stretch stretch;
            }
        """)
        
        
        
        self.element = QPixmap("./Backgrounds/cloudy/elementblur.png")
        
        self.mainbox = Card(self, self.element, self.s(self.windowsize[0]/2)-450, self.s(250), self.s(900), self.s(400))
        
        self.weather = Weather(current_location())
        print(current_location())
        self.weather.check()
        weather = self.weather.retrieve()
        print(weather)
        test = text(weather['weather'][0]['main'], "white", poppins("semi bold"), self.s(50), self)
        test.move(210, 100)
        
        self.condition_icon = QSvgWidget(self)
        self.condition_icon.load("./Icons/cloudy.svg")
        self.condition_icon.setGeometry(self.s(90), self.s(90), self.s(120), self.s(120))
        
        temperature = text(str(weather['main']['temp']), "white", poppins("semi bold"), self.s(50), self)
        temperature.move(510, 100)
        
        print(self.s(SIZE[0]), self.s(SIZE[1]))
        
        
    def s(self, value):
        return int(value*self.scale)
def main():
    QApplication.setAttribute(Qt.AA_DisableHighDpiScaling, True)
    
    app = QApplication(sys.argv)
    
    scale_point = scale(app)
    
    window = MainWindow(scale_point)
    
    
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()