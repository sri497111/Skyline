# Qt Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QPushButton, 
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase
from PyQt5 import QtWidgets

# Modules
from location import *
from retrieve import Weather
from ui_engine import text, button, poppins

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
        
        self.setStyleSheet("""
            QMainWindow {
                border-image: url('lightpartly.png') 0 0 0 0 stretch stretch;
            }
        """)
        
        self.weather = Weather("Phoenix")
        self.weather.check()
        test = text(self.weather.retrieve()['weather'][0]['main'], "white", poppins("semi bold"), self.s(50), self)
        test.move(self.s(100), self.s(100))
        
        self.setFixedSize(self.s(SIZE[0]), self.s(SIZE[1]))
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