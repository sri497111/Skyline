import tkinter
import pygame


def get_dpi():
    root = tkinter.Tk()
    dpi = int(root.winfo_fpixels('1i'))
    root.destroy()
    return dpi

def get_refresh_rate():
    pygame.init()
    pygame.display.set_mode((878, 550), pygame.HIDDEN)
    hertz = int(pygame.display.get_current_refresh_rate())
    pygame.quit()
    return hertz