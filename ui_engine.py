from PyQt5.QtWidgets import QLabel, QFrame, QSizePolicy, QApplication, QPushButton, QVBoxLayout
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap, QRegion, QPainterPath
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from system import *
import cairosvg


class Card(QFrame):
    def __init__(self, parent, pixmap, h=200, window_size=(878, 550)):
        super().__init__(parent)
        self.setFixedHeight(h)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        path = QPainterPath()
        
        self.pixmap = pixmap
        self.window_size = window_size
        
        self.scaled = self.pixmap.scaled(878, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
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

        self.path = QPainterPath()
        self.path.addRoundedRect(0, 0, w, h, 55, 55)
        self.setMask(QRegion(self.path.toFillPolygon().toPolygon()))
        
        self.updatePixmap()
        

class Button(Card):
    def __init__(self, parent, text, pixmap, w, h, font_size=64):
        super().__init__(parent, pixmap, h)
        self.setFixedHeight(h)
        self.setFixedWidth(w)
        
        
        self.p = parent
        self.pixmap = pixmap
        self.h = h
        self.w = w
        self.text = text
        
        self.font_fam = poppins("semi bold")
        button_font = QFont(self.font_fam, font_size)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.button = QPushButton(self.text, self)
        self.button.setStyleSheet(f"background: transparent; color: white; border: none; text-align: center; padding-bottom: 0px; margin: 0px; font-size: 48px;")
        self.button.setFont(button_font)
        
        self.button.setFixedHeight(self.h)
        self.button.setFixedWidth(self.w)
        self.button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.button)
        
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        w = self.width()
        h = self.height()
        
        self.button.setGeometry(0, 0, w, h)
        self.button.raise_()
        
def poppins(weight):
    weight = str(weight).title().replace(" ", "")
    font = QFontDatabase.addApplicationFont(f"./Font/poppins/Poppins-{weight}.ttf")
    if font == -1:
        print("Error loading font")
        return "Arial"
    else:
        return QFontDatabase.applicationFontFamilies(font)[0]
    



def text(text, color, font, size=20, parent=None):
    value = 96/get_dpi()
    label = QLabel(text, parent)
    label.setFont(QFont(font, size*value))
    label.setStyleSheet(f"color: {color}")
    
    if parent:
        label.show()
        label.adjustSize()
    
    return label

def svg(path, width, height):
    data = cairosvg.svg2png(url=path, output_width=width, output_height=height)
    pixmap = QPixmap()
    pixmap.loadFromData(data)
    
    icon_label = QLabel()
    icon_label.setFixedSize(width, height)
    icon_label.setPixmap(pixmap)
    return icon_label