import sys
import glob
import os
import pygame
import thread
import time
import steering_wheel_control as ControlSW

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
# import carla
# from carla import ColorConverter as cc
try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

HIDDEN = (0, 0, 0, 0)
TRANSPARENT = 0
VISIBLE = 255
RIGHT = 0
LEFT = 1
Yaxis = 600
Xaxis = 450
Roffset = 400
Rpos = (Xaxis + Roffset, Yaxis)
Lpos = (Xaxis, Yaxis)


class Guide(object):

    def __init__(self, driver):
        self.rarrow = pygame.image.load("../media/images/arrow_right_small.png").convert_alpha()
        self.larrow = pygame.image.load("../media/images/arrow_left_small.png").convert_alpha()
        self.timeout = 3
        self.left = False
        self.right = False
        self.driver = ControlSW.world.player
        thread.start_new_thread(self.autohide_arrow, ())
        return

    def _show_left(self):
        self.larrow.set_alpha(VISIBLE)
        ControlSW.display.blit(self.larrow, Lpos)
        self.left = True
        return self.left

    def _hide_left(self):
        self.larrow.set_alpha(TRANSPARENT)
        ControlSW.display.blit(self.larrow, Lpos)
        self.left = False
        return self.left

    def _show_right(self):
        self.rarrow.set_alpha(VISIBLE)
        ControlSW.display.blit(self.rarrow, Rpos)
        self.right = True
        return self.right

    def _hide_right(self):
        self.rarrow.set_alpha(TRANSPARENT)
        ControlSW.display.blit(self.rarrow, Rpos)
        self.right = False
        return self.right

    def blit_arrow(self, driver, location, direction, threshold=50):
        distance = _distance_from_driver(driver, location)
        if int(distance) < threshold:
            if direction == RIGHT:
                return self._show_right()
            else:
                return self._show_left()
        return False

    def autohide_arrow(self, timeout=5):
        while True:
            time.sleep(1)
            if self.left:
                time.sleep(timeout)
                self._hide_left()
            if self.right:
                time.sleep(timeout)
                self._hide_right()


def _distance_from_driver(driver, this_location):
    return this_location.distance(driver.get_location())
# ______________________________________________________________________________________________________________________
#   End of class Guide
# ______________________________________________________________________________________________________________________

locations = []
directions = []

def init():
    # define all locations for turns and directions


def render():
    return


def blit_arrow(guide, location, direction, threshold=50):
    distance = _distance_from_driver(driver, location)
    if int(distance) < threshold:
        if direction == RIGHT:
            return guide._show_right()
        else:
            return guide.show_left()
    return False
