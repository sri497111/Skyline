# Qt Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QPushButton, QVBoxLayout
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


SIZE = (975*0.9, 610*0.9)


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
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 5, 30 ,10)
        main_layout.addWidget(Card(widget, self.element, 200))
        main_layout.addWidget(Card(widget, self.element, 500))
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)
        
        
def main():   
    app = QApplication(sys.argv)
    
    window = MainWindow()
    
    
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()