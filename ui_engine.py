from PyQt5.QtWidgets import QLabel, QFrame, QSizePolicy, QApplication, QPushButton, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap, QRegion, QPainterPath, QPainter
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QRectF, QPropertyAnimation, QEasingCurve
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from system import *
from html2image import Html2Image
import os

dpi = get_dpi()


class Card(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, parent, pixmap, h=200, window_size=(878, 550), radius=55, raise_dark=True, window_widget=None):
        super().__init__(parent)
        self.setFixedHeight(h)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        path = QPainterPath()
        

        self.radius = radius
        self.raise_dark = raise_dark

        self.pixmap = pixmap
        self.window_size = window_size

        self.window_widget = window_widget
        
        self.scaled = self.pixmap.scaled(878, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.bg = QLabel(self)
        self.bg.setScaledContents(True)
        
        self.dark = QLabel(self)
        self.dark.setStyleSheet(f"""
                background: rgba(0,0,0,30);
                border-radius: {radius}px;
        """)
        
        
    def updatePixmap(self):
        h = self.height()
        w = self.width()
        
            
        card_global = self.mapToGlobal(self.rect().topLeft())

        target = self.window_widget if self.window_widget else self.window()
        window_global = target.mapToGlobal(target.rect().topLeft())

        relativex = card_global.x() - window_global.x()
        relativey = card_global.y() - window_global.y()
        crop = self.scaled.copy(relativex, relativey, w, h)
            
        self.bg.setPixmap(crop)
        
        if self.raise_dark:
            self.dark.raise_()
        else:
            self.dark.lower()
            self.bg.lower()
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        h = self.height()
        w = self.width()
        
        self.bg.setGeometry(0, 0, w, h)
        self.dark.setGeometry(0, 0, w, h)

        self.path = QPainterPath()
        self.path.addRoundedRect(0, 0, w, h, self.radius, self.radius)
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
    



def text(text, color, font, size=20, parent=None, padding=0, transparency=False):
    value = 96/dpi
    label = QLabel(text, parent)
    label.setFont(QFont(font, int(size*value)))
    if transparency: label.setStyleSheet(f"color: rgba(255,255,255,80); padding-left:{padding}")
    else: label.setStyleSheet(f"color: {color}; padding-left:{padding}")
    
    if parent:
        label.show()
        label.adjustSize()
    
    return label

def svg(path, width, height):
    svg_widget = QSvgWidget(path)
    svg_widget.setFixedSize(width, height)
    return svg_widget
    
def hover_svg(path, width, height):
    container = QFrame()

    padding = 14
    circle_size = max(width, height) + padding
    
    radius = circle_size // 2

    container.setFixedSize(circle_size, circle_size)

    container.setStyleSheet(f"""
    
            QFrame {{
                background: transparent;
                border-radius: {radius}px;
            }}
            QFrame:hover {{
                background: rgba(255, 255, 255, 30);
            }}  
    
    """)

    svg_widget = QSvgWidget(path)
    svg_widget.setFixedSize(width, height)
    svg_widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)
    
    layout = QVBoxLayout(container)
    layout.setAlignment(Qt.AlignCenter)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(svg_widget)
    
    return container

def get_map_preview(height, theme="light"):
    html = Html2Image(custom_flags=["--hide-scrollbar", "--disable-gpu"])
    
    if theme == "light":
        hfile = os.path.abspath("./map-light-preview.html")
    elif theme == "dark":
        hfile = os.path.abspath("./map-dark-preview.html")
    else:
        hfile = os.path.abspath("./map-light-preview.html")
    
    preview = "preview.png"
    
    html.screenshot(url=f"file:///{hfile}", save_as=preview, size=(778, int(height)))
    
    html_pixmap = QPixmap(preview)
    
    return html_pixmap


class Loading_Icon(QSvgWidget):
    def __init__(self, path, size=64):
        super().__init__(path)
        self.angle = 0
        
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.rend = QSvgRenderer(path)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        self.timer.start(10)  # 60FPS

    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        painter.translate(-self.width() / 2, -self.height() / 2)

        self.rend.render(painter, QRectF(self.rect()))

class Popup(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.setGeometry(0,0, self.main.width(), self.main.height())

        self.blur = Card(parent=self, pixmap=self.main.element, h=self.main.height(), window_size=(main_window.width(), main_window.height()), radius=0, raise_dark=True, window_widget=main_window)
        self.blur.setGeometry(self.rect())


        self.dim = QLabel(self)
        self.dim.setGeometry(self.rect())
        self.dim.setStyleSheet("background: rgba(0,0,0,0);")

        self.popup_layout = QVBoxLayout(self)
        self.popup_layout.setContentsMargins(50,0,50,0)
        self.popup_layout.setAlignment(Qt.AlignCenter)
        self.popup_layout.setSpacing(40)

        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        
        self.fade = QPropertyAnimation(self.opacity, b'opacity')
        self.fade.setDuration(200)
        self.fade.setStartValue(0.0)
        self.fade.setEndValue(1.0)

        self.show()
        self.raise_()
        self.fade.start()

    def mousePressEvent(self, event):
        if self.childAt(event.pos()) in (None, self.blur, self.dim):
            self.exit_popup()
        super().mousePressEvent(event)
    
    def wheelEvent(self, event):
        event.accept()
    
    def exit_popup(self):
        self.fade.stop()
        self.fade.setStartValue(self.opacity.opacity())
        self.fade.setEndValue(0.0)
        self.fade.finished.connect(self.deleteLater)
        self.fade.start()
        
        
