import sys
import glob
import os
import pygame
import thread
import datetime
import time
import math
import weakref
import steering_wheel_control as ControlSW
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla
from carla import ColorConverter as cc
try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

HIDDEN = (0,0,0,0)
TRANSPARENT = 0
VISIBLE = 255

class Guide(object):

    def __init__(self, display, driver):
        self.rarrow = pygame.image.load("../media/images/arrow_right_small.png").convert_alpha()
        self.larrow = pygame.image.load("../media/images/arrow_left_small.png").convert_alpha()
        self.display = display
        self.driver = driver
        self.timeout = 3
        self.rarrow.set_alpha(TRANSPARENT)    #initial state is transparent
        self.larrow.set_alpha(TRANSPARENT)    #initial state is transparent
        self.display.blit(self.rarrow, (850, 600))
        self.display.blit(self.rarrow, (450, 600))
        pygame.display.update()

    def show_left(self, timeout=0):
        self.larrow.set_alpha(VISIBLE)
        pygame.display.update()
        if timeout:
            thread.start_new_thread(time.sleep, (timeout,))
            self.rarrow.set_alpha(TRANSPARENT)
            pygame.display.update()
        return

    def show_right(self, timeout=0):
        self.rarrow.set_alpha(VISIBLE)
        pygame.display.update()
        if timeout:
            thread.start_new_thread(time.sleep, (timeout,))
            self.rarrow.set_alpha(TRANSPARENT)
            pygame.display.update()
        return

    def hide(self):
        self.larrow.set_alpha(TRANSPARENT)
        self.rarrow.set_alpha(TRANSPARENT)
        game.display.update()
        return



