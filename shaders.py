from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage
from OpenGL.GL import *
import time
import sys

def load_shader(shader_file):
    with open(shader_file, 'r', encoding='utf-8') as f:
        shader_source = f.read()
        return shader_source
    
RAINVERTEXSHADER = load_shader('./Shaders/rain.vert')
RAINFRAGSHADER = load_shader('./Shaders/rain.frag')

# Creates an OpenGL instance inside of QWidget reads pixmap texture, rasterizes it, loads it and then applies the Vertex and Fragment Shaders to it. 
# Does this every 16 ms.
class RainShaderOverlay(QOpenGLWidget):
    def __init__(self, parent=None, pixmap=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.start_time = time.time()
        self.img_width = float(self.pixmap.width())
        self.img_height = float(self.pixmap.height())

        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
        
        if hasattr(self, 'program'):
            self.load_texture()
    
    def compile_shader(self, source, shader_type):
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)

        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            log = glGetShaderInfoLog(shader)
            type_shade = "VERTEX" if shader_type == GL_VERTEX_SHADER else "FRAGMENT"
            raise RuntimeError(f"Failed to compile {type_shade} shader:\n{log}")
        return shader
    
    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)

        self.program = glCreateProgram()
        glAttachShader(self.program, self.compile_shader(RAINVERTEXSHADER, GL_VERTEX_SHADER))
        glAttachShader(self.program, self.compile_shader(RAINFRAGSHADER, GL_FRAGMENT_SHADER))
        glLinkProgram(self.program)

        if not glGetProgramiv(self.program, GL_LINK_STATUS):
            raise RuntimeError(glProgramInfoLog(self.program).decode('utf-8'))
        
        glUseProgram(self.program)

        vertices = [-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0]

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, (GLfloat * len(vertices))(*vertices), GL_STATIC_DRAW)

        self.texture_id = glGenTextures(1)

        if self.pixmap:
            self.load_texture()

    def load_texture(self):
        if not self.pixmap:
            return
        
        image = self.pixmap.toImage().convertToFormat(QImage.Format_RGBA8888)
        #image = image.mirrored(False, True)

        self.img_width = float(image.width())
        self.img_height = float(image.height())

        ptr = image.constBits()
        ptr.setsize(image.byteCount())
        image_data = bytes(ptr)

        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width(), image.height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.program)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        position_attr = glGetAttribLocation(self.program, "position")
        glEnableVertexAttribArray(position_attr)
        glVertexAttribPointer(position_attr, 2, GL_FLOAT, GL_FALSE, 0, None)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, getattr(self, 'texture_id', 0))
        glUniform1i(glGetUniformLocation(self.program, "iChannel0"), 0)

        current_time = time.time() - self.start_time
        glUniform1f(glGetUniformLocation(self.program, "iTime"), current_time)
        glUniform2f(glGetUniformLocation(self.program, "iResolution"), float(self.width()), float(self.height()))
        glUniform2f(glGetUniformLocation(self.program, "iChannelResolution"), self.img_width, self.img_height)

        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

