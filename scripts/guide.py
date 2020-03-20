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
DRIVER_VEHICLE = "tt"
Yaxis = 600
Xaxis = 450
Roffset = 400
Rpos = (Xaxis+Roffset, Yaxis)
Lpos = (Xaxis, Yaxis)

class Guide(object):

    def __init__(self, driver):
        self.rarrow = pygame.image.load("../media/images/arrow_right_small.png").convert_alpha()
        self.larrow = pygame.image.load("../media/images/arrow_left_small.png").convert_alpha()
        self.timeout = 3
        self.shown = False
        self.driver = driver
        # pygame.display.update()

    def show_left(self, timeout=0):
        ControlSW.display.blit(self.larrow, Lpos)
        self.shown = True
        # pygame.display.update()
        if timeout:
            thread.start_new_thread(time.sleep, (timeout,))
            self.rarrow.set_alpha(TRANSPARENT)
            # self.shown = False
            # pygame.display.update()
        return

    def show_right(self, timeout=0):
        ControlSW.display.blit(self.rarrow, Rpos)
        pygame.display.update()
        return


    def blit_arrow_location(self, arrow, location, threshold=50):
        end_threshold = int(threshold / 5)
        while True:
            dist = self._distance_from_driver(self.driver, location)
            print(dist)
            time.sleep(.1)
            if int(dist) < threshold:
                print("----Blit arrow by location activated")



    def blit_arrow(self, arrow, timeout=0):
        if arrow == RIGHT:
            self.rarrow.set_alpha(VISIBLE)
            ControlSW.display.blit(self.rarrow, Rpos)
            self.shown = True
            # time.sleep(timeout)
            # self.rarrow.set_alpha(TRANSPARENT)
            # ControlSW.display.blit(self.rarrow, Rpos)
        else:
            self.larrow.set_alpha(VISIBLE)
            ControlSW.display.blit(self.larrow, Lpos)
            self.shown = True
            # time.sleep(timeout)
            # self.larrow.set_alpha(TRANSPARENT)
            # ControlSW.display.blit(self.larrow, Lpos)
        # self.shown = False
        return



    @staticmethod
    def _distance_from_driver(driver, this_location):
        return this_location.distance(driver.get_location())



