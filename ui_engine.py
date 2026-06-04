from PyQt5.QtWidgets import QLabel, QFrame
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap, QRegion, QPainterPath
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt



class Card(QFrame):
    def __init__(self, parent, pixmap, x, y, w, h):
        super().__init__(parent)
        self.setGeometry(x, y, w, h)
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 55, 55)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))
        
        scaled = pixmap.scaled(parent.width(), parent.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.crop = scaled.copy(x, y, w, h)
        
        self.bg = QLabel(self)
        self.bg.setGeometry(0, 0, w, h)
        self.bg.setScaledContents(True)
        self.bg.setPixmap(self.crop)
        
        
        
        self.bg.show()
        
        self.dark = QLabel(self)
        self.dark.setGeometry(0, 0, w, h)
        self.dark.setStyleSheet("""
                background: rgba(0,0,0,30);
                border-radius: 55px;
        """)
        self.dark.raise_()
        self.show()

def poppins(weight):
    weight = str(weight).title().replace(" ", "")
    font = QFontDatabase.addApplicationFont(f"./Font/poppins/Poppins-{weight}.ttf")
    if font == -1:
        print("Error loading font")
        return "Arial"
    else:
        return QFontDatabase.applicationFontFamilies(font)[0]
    

def text(text, color, font, size=20, parent=None):
    label = QLabel(text, parent)
    label.setFont(QFont(font, size))
    label.setStyleSheet(f"color: {color}")
    if parent:
        label.show()
        label.adjustSize()
    return label

def button():
    pass