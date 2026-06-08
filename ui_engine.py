from PyQt5.QtWidgets import QLabel, QFrame, QSizePolicy, QApplication
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap, QRegion, QPainterPath
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from system import *



class Card(QFrame):
    def __init__(self, parent, pixmap, h=200, window_size=(878, 550)):
        super().__init__(parent)
        self.setFixedHeight(h)
        
        
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        path = QPainterPath()
        
        self.pixmap = pixmap
        self.window_size = window_size
        
        self.scaled = self.pixmap.scaled(878, 550, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        
        self.bg = QLabel(self)
        self.bg.setScaledContents(True)
        
        
        
        self.dark = QLabel(self)
        self.dark.setStyleSheet("""
                background: rgba(0,0,0,30);
                border-radius: 55px;
        """)
        
        
    def updatePixmap(self):
        h = self.height()
        w = self.width()
        
            
        card_global = self.mapToGlobal(self.rect().topLeft())
        window_global = self.window().mapToGlobal(self.window().rect().topLeft())
        relativey = card_global.y() - window_global.y()
        crop = self.scaled.copy(0, relativey, w, h)
            
        self.bg.setPixmap(crop)
        self.dark.raise_()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        h = self.height()
        w = self.width()
        
        self.bg.setGeometry(0, 0, w, h)
        self.dark.setGeometry(0, 0, w, h)

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 55, 55)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))
        
        self.updatePixmap()
        
        
        
        
def poppins(weight):
    weight = str(weight).title().replace(" ", "")
    font = QFontDatabase.addApplicationFont(f"./Font/poppins/Poppins-{weight}.ttf")
    if font == -1:
        print("Error loading font")
        return "Arial"
    else:
        return QFontDatabase.applicationFontFamilies(font)[0]
    



def text(text, color, font, size=20, parent=None):
    value = get_dpi()/96
    label = QLabel(text, parent)
    label.setFont(QFont(font, size*value))
    label.setStyleSheet(f"color: {color}")
    
    if parent:
        label.show()
        label.adjustSize()
    
    return label

def button():
    pass