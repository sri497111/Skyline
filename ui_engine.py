from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5 import QtWidgets

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