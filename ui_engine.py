from PyQt5.QtWidgets import QLabel, QFrame, QSizePolicy
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap, QRegion, QPainterPath
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt



class Card(QFrame):
    def __init__(self, parent, pixmap, h=200):
        super().__init__(parent)
        self.setFixedHeight(h)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        path = QPainterPath()
        
        self.pixmap = pixmap
        
        self.bg = QLabel(self)
        self.bg.setScaledContents(True)
        
        
        
        self.dark = QLabel(self)
        self.dark.setStyleSheet("""
                background: rgba(0,0,0,30);
                border-radius: 55px;
        """)
        
        
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        
        self.bg.setGeometry(0, 0, w, h)
        self.dark.setGeometry(0, 0, w, h)

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 55, 55)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))
        
        if self.parent():
            scaled = self.pixmap.scaled(self.parent().width(), self.parent().height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.crop = scaled.copy(self.x(), self.y(), w, h)
            self.bg.setPixmap(self.crop)
        self.bg.show()
        self.dark.raise_()
        
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