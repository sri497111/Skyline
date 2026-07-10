import threading
import tkinter
import pygame
import socket

# Uses tk to get the users DPI settings
def get_dpi():
    root = tkinter.Tk()
    dpi = int(root.winfo_fpixels('1i'))
    root.destroy()
    return dpi

# Opens a pygame instance quickly and checks refresh rate
def get_refresh_rate():
    pygame.init()
    pygame.display.set_mode((878, 550), pygame.HIDDEN)
    hertz = int(pygame.display.get_current_refresh_rate())
    pygame.quit()
    return hertz

# Does a intenet connection check on another thread so it won't freeze the app
def internet_check(callback):
    def worker():
        try:
            socket.setdefaulttimeout(2)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('8.8.8.8', 53))
            callback(True)
        except OSError:
            callback(False)

    threading.Thread(target=worker, daemon=True).start()
