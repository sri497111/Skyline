from PyQt5.QtWidgets import QHBoxLayout, QLabel, QFrame, QSizePolicy, QApplication, QPushButton, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import QSize, QTimer, Qt, pyqtSignal, QRectF, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QPoint, QEvent, QRect
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap, QRegion, QPainterPath, QPainter, QBrush, QColor, QImage
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from PyQt5 import QtWidgets

from shaders import RainShaderOverlay
from system import *

import requests
import json
import math
import os

dpi = get_dpi()

settings_file = "./settings.json"

def check_theme():
    with open(settings_file, "r") as settings:
        data = json.load(settings)
        theme = data.get("theme", {})
        main = theme.get("main") if isinstance(theme, dict) else theme

        return 0 if main == "dark" else 1

class Card(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, parent, pixmap, h=200, window_size=(878, 550), radius=55, raise_dark=True, window_widget=None, rain_effect=False):
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
        theme = check_theme()
        color = "white" if theme == 0 else "black"
        
        self.highlight = QLabel(self)
        self.highlight.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.highlight.setStyleSheet(f"""
                border: 3px solid {color};
                border-radius: {radius};
                background: transparent;
        """)
        self.highlight.hide()
        

        if rain_effect:
            self.rain_shader = RainShaderOverlay(self, self.pixmap)
            self.rain_shader.move(0, 0)
            self.rain_shader.show()
            self.rain_shader.raise_()

    def updatePixmap(self):
        h = self.height()
        w = self.width()

        if w <= 0 or h <= 0: return

        target = self.window_widget if self.window_widget else self.window()

        if not target or target == self:
            target_w = self.window_size[0]
            target_h = self.window_size[1]
        else:
            target_w = target.width() if target.width() > 0 else self.window_size[0] if self.window_size else target.width()
            target_h = target.height() if target.height() > 0 else self.window_size[1] if self.window_size else target.height()
        
        if getattr(self, '_cached_tw', None) == target_w and getattr(self, '_cached_th', None) == target_h:
            self._cached_tw = target_w
            self._cached_th = target_h
            self.scaled = self.pixmap.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.offset_x = (self.scaled.width() - target_w) // 2
            self.offset_y = (self.scaled.height() - target_h) // 2
        
        if not hasattr(self, 'scaled'): return  

        card_global = self.mapToGlobal(self.rect().topLeft())

        window_global = target.mapToGlobal(target.rect().topLeft())

        relativex = card_global.x() - window_global.x()
        relativey = card_global.y() - window_global.y()
        
        source_rect = QRect(relativex, relativey, w, h)
        valid_rect = source_rect.intersected(self.scaled.rect())

        crop = QPixmap(w, h)
        crop.fill(Qt.transparent)

        if not valid_rect.isEmpty():
            sub_pixmap = self.scaled.copy(valid_rect)
            painter = QPainter(crop)

            dx = valid_rect.x() - relativex
            dy = valid_rect.y() - relativey

            painter.drawPixmap(dx, dy, sub_pixmap)

            if dx > 0:
                left_edge = sub_pixmap.copy(0, 0, 1, sub_pixmap.height())
                painter.drawTiledPixmap(0, dy, dx, sub_pixmap.height(), left_edge)
            if dx + valid_rect.width() < w:
                right_edge = sub_pixmap.copy(sub_pixmap.width() - 1, 0, 1, sub_pixmap.height())
                painter.drawTiledPixmap(dx + valid_rect.width(), dy, w - dx - valid_rect.width(), sub_pixmap.height(), right_edge)

            if dy > 0:
                top_edge = sub_pixmap.copy(0, 0, sub_pixmap.width(), 1)
                painter.drawTiledPixmap(dx, 0, sub_pixmap.width(), dy, top_edge)
            if dy + valid_rect.height() < h:
                bottom_edge = sub_pixmap.copy(0, sub_pixmap.height() - 1, sub_pixmap.width(), 1)
                painter.drawTiledPixmap(dx, dy + valid_rect.height(), sub_pixmap.width(), h - dy - valid_rect.height(), bottom_edge)

            
            if dx > 0 or dx + valid_rect.width() < w or dy > 0 or dy + valid_rect.height() < h:
                painter.fillRect(0,0, dx, dy, sub_pixmap.copy(0, 0, 1, 1).toImage().pixelColor(0, 0))
            if dx + valid_rect.width() < w and dy > 0:
                painter.fillRect(dx+valid_rect.width(), 0, w - (dx + valid_rect.width()), dy, sub_pixmap.copy(sub_pixmap.width() - 1, 0, 1, 1).toImage().pixelColor(0, 0))
            if dx > 0 and dy + valid_rect.height() < h:
                painter.fillRect(0, dy+valid_rect.height(), dx, h - (dy + valid_rect.height()), sub_pixmap.copy(0, sub_pixmap.height() - 1, 1, 1).toImage().pixelColor(0, 0))
            if dx + valid_rect.width() < w and dy + valid_rect.height() < h:
                painter.fillRect(dx+valid_rect.width(), dy+valid_rect.height(), w - (dx + valid_rect.width()), h - (dy + valid_rect.height()), sub_pixmap.copy(sub_pixmap.width() - 1, sub_pixmap.height() - 1, 1, 1).toImage().pixelColor(0, 0))

            painter.end()
        
        self.bg.setPixmap(crop)

        if hasattr(self, 'rain_shader'):
            self.rain_shader.set_pixmap(crop)
        
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
        self.highlight.setGeometry(0,0,self.width(),self.height())

        if hasattr(self, 'rain_shader'):
            self.rain_shader.setGeometry(0, 0, w, h) 

        self.path = QPainterPath()
        self.path.addRoundedRect(0, 0, w, h, self.radius, self.radius)
        self.setMask(QRegion(self.path.toFillPolygon().toPolygon()))
        
        self.updatePixmap()
    
    def alternate(self, index):
        if index == 0:
            self.dark.setStyleSheet(f"""
                    background: rgba(0,0,0,30);
                    border-radius: {self.radius}px;
            """)

        else:
            self.dark.setStyleSheet(f"""
                    background: rgba(255,255,255,30);
                    border-radius: {self.radius}px;
            """)
    
    def update_highlight_theme(self):
        theme = check_theme()
        color = "white" if theme == 0 else "black"
        
        self.highlight = QLabel(self)
        self.highlight.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.highlight.setStyleSheet(f"""
                border: 3px solid {color};
                border-radius: {self.radius};
                background: transparent;
        """)
        self.highlight.hide()


        
class RegularCard(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, parent, pixmap, h=200, window_size=(878, 550), radius=55, raise_dark=True, window_widget=None, rain_effect=False):
        super().__init__(parent)
        self.setFixedHeight(h)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        path = QPainterPath()
        
        self.rain_effect = rain_effect

        self.radius = radius
        self.raise_dark = raise_dark

        self.pixmap = pixmap
        self.window_size = window_size

        self.window_widget = window_widget
        
        self.scaled = self.pixmap.scaled(878, 550, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        
        self.bg = QLabel(self)
        self.bg.setScaledContents(True)
        
        self.dark = QLabel(self)
        self.dark.setStyleSheet(f"""
                background: rgba(0,0,0,30);
                border-radius: {radius}px;
        """)
        theme = check_theme()
        color = "white" if theme == 0 else "black"
        
        self.highlight = QLabel(self)
        self.highlight.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.highlight.setStyleSheet(f"""
                border: 3px solid {color};
                border-radius: {radius};
                background: transparent;
        """)
        self.highlight.hide()

        if rain_effect:
            self.rain_shader = RainShaderOverlay(self, self.pixmap)
            self.rain_shader.move(0, 0)
            self.rain_shader.show()
            self.rain_shader.raise_()

        
        
    def updatePixmap(self):
        h = self.height()
        w = self.width()
        
        scaled = self.pixmap.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        crop = scaled.copy(0,0, w,h)
        self.bg.setPixmap(crop)

        if self.rain_effect:
            self.rain_shader.set_pixmap(crop)
            self.rain_shader.setGeometry(0, 0, w, h)

        
        if self.raise_dark:
            self.dark.raise_()
        else:
            self.dark.lower()
            self.bg.lower()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)

        if event.size() == event.oldSize():
            return
        
        h = self.height()
        w = self.width()
        
        self.bg.setGeometry(0, 0, w, h)
        self.dark.setGeometry(0, 0, w, h)
        self.highlight.setGeometry(0,0,self.width(),self.height())

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


    svg_widget = QSvgWidget(path, container)
    svg_widget.setFixedSize(width, height)
    svg_widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    x = (circle_size - width) // 2
    y = (circle_size - height) // 2
    svg_widget.move(x, y)
    
    svg_widget._orig_geo = QRect(x, y, width, height)
    
    return container

def hover_text(parent, pixmap, word, font_size):
    container = Card(parent, pixmap, 40, radius=20)
    container.setFixedWidth(150)
    container.setCursor(Qt.PointingHandCursor)

    container_layout = QHBoxLayout(container)

    words = text(str(word), "white", poppins("semi bold"), font_size, container)

    container_layout.addWidget(words, alignment=Qt.AlignCenter)

    return container


def get_map_preview(lat, lon, width=778, height=305, theme="light", precise=True):
    lat, lon = float(lat), float(lon)

    zoom = 11 if precise else 9
    n = 2.0 ** int(zoom)

    xtile = float((lon + 180.0) / 360.0 * n)
    ytile = float((1.0 - math.log(math.tan(math.radians(lat)) + (1.0 / math.cos(math.radians(lat)))) / math.pi) / 2.0 * n)
    
    top_left_x = (xtile * 256) - (width/2)
    top_left_y = (ytile * 256) - (height/2)

    start_x, end_x = int(top_left_x // 256), int((top_left_x + width) // 256)
    start_y, end_y = int(top_left_y // 256), int((top_left_y + height) // 256)

    pixmap = QPixmap(width, height)

    if theme == "dark": pixmap.fill(QColor("#0f172a")); path = "dark_all"
    else: pixmap.fill(QColor("#cbd5e1")); path = "rastertiles/voyager"

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    DATA_KEY = "7dd61afc5903f81a45839eb528dcbabd"

    for x in range(start_x, end_x + 1):
        for y in range(start_y, end_y + 1):
            dest_x = (x * 256) - top_left_x
            dest_y = (y * 256) - top_left_y

            rect = QRectF(dest_x, dest_y, 256, 256)
            
            base_url = f"https://a.basemaps.cartocdn.com/{path}/{zoom}/{x}/{y}.png"
            req_base = requests.get(base_url)

            if req_base.status_code == 200:
                image = QImage()
                image.loadFromData(req_base.content)
                painter.setOpacity(0.9)
                painter.drawImage(rect, image)
                painter.setOpacity(1.0)
    
    if precise:
        cx, cy = width / 2.0, height / 2.0

        painter.setPen(Qt.NoPen)

        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QRectF(cx - 10, cy - 10, 20, 20))

        painter.setBrush(QColor("#3693ff"))
        painter.drawEllipse(QRectF(cx - 5, cy - 5, 10, 10))

        painter.end()
    
    else:
        painter.setPen(Qt.NoPen)
        painter.end()
        

    return pixmap



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
    def __init__(self, main_window, clear=True):
        super().__init__(main_window)
        self.main = main_window
        self.setGeometry(0,0, self.main.width(), self.main.height())



        if clear:
            self.blur = Card(parent=self, pixmap=self.main.element, h=self.main.height(), window_size=(main_window.width(), main_window.height()), radius=0, raise_dark=True, window_widget=main_window)
            self.blur.setGeometry(self.rect())

            self.dim = QLabel(self)
            self.dim.setGeometry(self.rect())
            self.dim.setStyleSheet("background: rgba(0,0,0,0);")
        
        else:
            # For the ability for flat themes

            app_theme = check_theme()

            if app_theme == 0:
                self.pixmap = QPixmap("./Backgrounds/dark-theme.png")
            else:
                self.pixmap = QPixmap("./Backgrounds/light-theme.png")

            # Not actually blur but just for the sake of not changing it too much

            self.blur = Card(parent=self, pixmap=self.pixmap, h=self.main.height(), window_size=(main_window.width(), main_window.height()), radius=0, raise_dark=True, window_widget=main_window)
            self.blur.setGeometry(self.rect())

            self.dim = QLabel(self)
            self.dim.setGeometry(self.rect())
            self.dim.setStyleSheet("background: rgba(0,0,0,0);")

        self.popup_layout = QVBoxLayout(self)
        self.popup_layout.setContentsMargins(50,0,50,0)
        self.popup_layout.setAlignment(Qt.AlignCenter)
        self.popup_layout.setSpacing(40)

        self.opacity = QGraphicsOpacityEffect(self)
        self.opacity.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity)
        
        self.fade = QPropertyAnimation(self.opacity, b'opacity')
        self.fade.setDuration(200)
        self.fade.setStartValue(0.0)
        self.fade.setEndValue(1.0)

        self.show()
        self.raise_()
        
        QTimer.singleShot(5, self.fade.start)

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
    

class RadioButton(QWidget):
    #-----------------------------------------------------------------------------------------------
    #| Option define name (passed as text(arg))                            | Option 1 | Option 2   |
    #-----------------------------------------------------------------------------------------------

    # This class is limited as it is a mini class with a limit of 2 options. 
    # Selected can be 0 for option 1, or 1 for option 2. Default is None as in none selected.
    # I animated it so that the indicator will slide

    valueChanged = pyqtSignal(int)
    def __init__(self, parent, option_name, options, selected=0, element=None, functions=None):
        super().__init__(parent)
        self.selected = selected
        self.option_text = option_name
        self.options = options # --> options is a list, formatted as [option_1, option_2]
        self.positions = [0, 100]

        if functions is None:
            functions = [None, None]
        
        self.function1 = functions[0]
        self.function2 = functions[1]

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)

        # This creates the main pill shape for the buttons
        self.radio_card = Card(self, element, 70, radius=35, raise_dark=False)
        self.radio_card.dark.setStyleSheet("background: rgba(0,0,0,70); border-radius: 35px;")

        self.main_layout.addWidget(self.radio_card)

        self.radio_layout = QHBoxLayout(self.radio_card)
        self.radio_layout.setContentsMargins(30,0,30,0)

        self.option_name = text(self.option_text, "white", poppins("semi bold"), 15, self.radio_card)

        self.radio_layout.addWidget(self.option_name, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        self.container = QFrame(self.radio_card)
        self.container.setFixedSize(200, 50)
        self.container.setStyleSheet("background: rgba(255,255,255,30); border-radius: 25px;")
        self.container.installEventFilter(self)

        self.indicator = QFrame(self.container)
        self.indicator.setFixedSize(100, 50)
        self.indicator.setStyleSheet("background: rgba(255,255,255,60); border-radius: 25px;")
        self.indicator.move(self.positions[selected], 0)

        self.radio_layout.addWidget(self.container, alignment=Qt.AlignRight | Qt.AlignVCenter)

        self.anim = QPropertyAnimation(self.indicator, b"pos")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        self.option1 = QPushButton(self.options[0], self.container)
        #self.option1.setFixedSize(100, 50)

        self.option2 = QPushButton(self.options[1], self.container)
        #self.option2.setFixedSize(100, 50)

        for i, btn in enumerate([self.option1, self.option2]):
            btn.setGeometry(self.positions[i], 0, 100, 50)
            btn.setFont(QFont(poppins("semi bold"), 10))
            btn.setStyleSheet("background: transparent; color: white; border: none;")
            btn.setCursor(Qt.PointingHandCursor)
            btn.installEventFilter(self)
            
            if self.function1 and self.function2:
                btn.clicked.connect(self.function1 if i == 0 else self.function2)

        self.container.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            if obj == self.option1: self.animate(0)
            elif obj == self.option2: self.animate(1)

        elif event.type() == QEvent.Leave and obj == self.container:
            self.animate(self.selected)

        elif event.type() == QEvent.MouseButtonPress and obj in (self.option1, self.option2):
            idx = 0 if obj == self.option1 else 1
            if self.selected != idx:
                self.selected = idx
                self.valueChanged.emit(idx)
            self.animate(idx)

        return super().eventFilter(obj, event)
    
    def animate(self, index):
        self.anim.stop()
        self.anim.setEndValue(QPoint(self.positions[index], 0))
        self.anim.start()


def mouse_press_dim(obj, callback=None):
    def wrapper(event):
        fade = obj.graphicsEffect()
        
        if not isinstance(fade, QGraphicsOpacityEffect):
            fade = QGraphicsOpacityEffect(obj)
            obj.setGraphicsEffect(fade)
        
        svg_child = obj.findChild(QSvgWidget)
        
        if not svg_child:
            if callback:
                callback(event)
            return

        if not hasattr(obj, "_orig_geo"):
            obj._orig_geo = svg_child.geometry()

        fade_anim = QPropertyAnimation(fade, b"opacity")
        fade_anim.setDuration(200)
        fade_anim.setStartValue(1.0)
        fade_anim.setEndValue(0.5)
        fade_anim.setEasingCurve(QEasingCurve.InOutQuad)

        

        obj._press_anim = QParallelAnimationGroup()
        obj._press_anim.addAnimation(fade_anim)
        obj._press_anim.start()

        if callback:
            callback(event)
    
    return wrapper

def mouse_release_dim(obj, callback=None):
    def wrapper(event):
        fade = obj.graphicsEffect()
        
        if not isinstance(fade, QGraphicsOpacityEffect):
            fade = QGraphicsOpacityEffect(obj)
            obj.setGraphicsEffect(fade)

        svg_child = obj.findChild(QSvgWidget)
        
        if not svg_child:
            if callback:
                callback(event)
            return

        if not hasattr(obj, "_orig_geo"):
            obj._orig_geo = svg_child.geometry()

        
        fade_anim = QPropertyAnimation(fade, b"opacity")
        fade_anim.setDuration(200)
        fade_anim.setStartValue(fade.opacity())
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.OutBack)

        obj._release_anim = QParallelAnimationGroup()
        obj._release_anim.addAnimation(fade_anim)
        
        if callback:
            obj._release_anim.finished.connect(lambda: QTimer.singleShot(5, lambda: callback(event)))

        obj._release_anim.start()
    
    return wrapper

class WeatherCard(RegularCard):
    def __init__(self, parent, background, location_name="Cupertino", lat=0, lon=0, current_condition="Clear", current_temp=72, hi=67, low=99, description=""):
        super().__init__(parent, background, 200, rain_effect=True if "rain" in current_condition.lower() else False)

        self.setFixedWidth(600)
        self.setCursor(Qt.PointingHandCursor)


        self.cond = str(current_condition)

        self.batch_select = False

        self.location_name = location_name
        self.lat = lat
        self.lon = lon
        self.cond = current_condition
        self.description = description
        self.current_temp = current_temp
        self.hi = hi
        self.low = low

        print(self.description)

        self.weather_layout = QHBoxLayout(self)
        self.weather_layout.setContentsMargins(50,25,50,25)
        self.weather_layout.setSpacing(0)


        icon_and_name = QWidget()
        icon_and_name_layout = QVBoxLayout(icon_and_name)
        icon_and_name_layout.setContentsMargins(0,0,0,0)
        icon_and_name_layout.setSpacing(0)

        self.location_name = text(location_name, "white", poppins("Semi bold"), 20, self)
        self.location_name.setStyleSheet(self.location_name.styleSheet() + "; margin-top: 0px; padding-top: 0px;")  
        
        icon_and_name_layout.addWidget(self.location_name, alignment=Qt.AlignTop | Qt.AlignLeft)

        self.condition_label = text(str(self.cond), "white", poppins("semi bold"), 15, self)
        self.condition_label.setStyleSheet(self.condition_label.styleSheet() + "; margin-top: 0px; padding-top: 0px;")
        icon_and_name_layout.addWidget(self.condition_label, alignment=Qt.AlignTop | Qt.AlignLeft)

        icon_and_name_layout.addStretch(1)

        self.weather_layout.addWidget(icon_and_name, alignment=Qt.AlignTop)
        self.weather_layout.addStretch(1)

        if "clear" in self.cond.lower():
            self.pixmap = QPixmap("./Backgrounds/clear/dash1.png")
        elif "cloud" in self.cond.lower() and "few" in description.lower() or "scattered" in description.lower():
            self.pixmap = QPixmap("./Backgrounds/partly/dash2.png")
            self.cond = "Partly Cloudy"
            self.condition_label.setText("Partly Cloudy")
        elif "cloud" in self.cond.lower():
            self.pixmap = QPixmap("./Backgrounds/cloudy/dash1.png")
        elif "rain" in self.cond.lower():
            self.pixmap = QPixmap("./Backgrounds/cloudy/dash1.png")

        
        temp = QWidget()
        temp_layout = QVBoxLayout(temp)
        temp_layout.setContentsMargins(0,0,0,0)
        temp_layout.setSpacing(0)

        temp_string = f'{str(self.current_temp)}\u00b0'
        self.temp_label = text(temp_string, "white", poppins("semi bold"), 72, self)
        self.temp_label.setStyleSheet(self.temp_label.styleSheet() + "; margin-top: 0px; padding-top: 0px;")
        temp_layout.addWidget(self.temp_label, alignment=Qt.AlignTop | Qt.AlignCenter)

        high_low = f"H: {str(self.hi)}\u00b0 / L: {str(self.low)}\u00b0"
        self.hi_lo_label = text(high_low, "white", poppins("semi bold"), 15, self)
        self.hi_lo_label.setStyleSheet(self.hi_lo_label.styleSheet() + "; margin-top: 0px; padding-right: 10px;")
        temp_layout.addWidget(self.hi_lo_label, alignment=Qt.AlignTop | Qt.AlignCenter)
        
        temp_layout.addStretch(1)

        self.weather_layout.addWidget(temp)

    def updateWeatherBG(self):

        if "-" not in self.cond:
            description = getattr(self, "description", "")

            if "clear" in self.cond.lower():
                self.pixmap = QPixmap("./Backgrounds/clear/dash1.png")
            elif "cloud" in self.cond.lower() and "few" in description.lower() or "scattered" in description.lower():
                self.pixmap = QPixmap("./Backgrounds/partly/dash2.png")
                self.cond = "Partly Cloudy"
                self.condition_label.setText("Partly Cloudy")
            elif "cloud" in self.cond.lower():
                self.pixmap = QPixmap("./Backgrounds/cloudy/dash1.png")
            elif "rain" in self.cond.lower():
                self.pixmap = QPixmap("./Backgrounds/cloudy/dash1.png")
            

        self.updatePixmap()

