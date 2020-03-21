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

    def __init__(self):
        self.rarrow = pygame.image.load("../media/images/arrow_right_small.png").convert_alpha()
        self.larrow = pygame.image.load("../media/images/arrow_left_small.png").convert_alpha()
        self.left = False
        self.right = False
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

    def blit_arrow(self, location, direction, threshold=50):
        distance = distance_from_driver(location)
        if int(distance) < threshold:
            if direction == RIGHT:
                return self._show_right()
            else:
                return self._show_left()
        else:
            print("[Warning] Threshold %d not reached, distance is %d" % (threshold, distance))  # debug

    def autohide_arrow(self, timeout=5):
        while True:
            time.sleep(1)
            if self.left:
                time.sleep(timeout)
                self._hide_left()
            if self.right:
                time.sleep(timeout)
                self._hide_right()


def distance_from_driver(this_location):
    return this_location.distance(ControlSW.world.player.get_location())
# ______________________________________________________________________________________________________________________
#   End of class Guide
# ______________________________________________________________________________________________________________________


locations = [( 219,  10,0),(  10, 193,0),(   6, 145,0),( 170,  78,0),
             ( 219,  62,0),(  22,-203,0),(  0, -147,0),( 137,-128,0),
             ( 149, -17,0),(  93,  -7,0),(  84,-121,0),(  20,-137,0),
             ( -23, -11,0),( -64,  -3,0),(-128,  44,0),( -98,-136,0),
             ( 230,  43,0)]
directions = [1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1]
ndx = 0


def render(guide):
    global locations, directions, ndx
    if ndx > 16:
        print("[Error] The index for guide is out of bounds: ", ndx, ". Exit.")
        return
    if not guide.blit_arrow(ControlSW.world.player, locations[ndx], directions[ndx]):
        print("[Warning] Function render in Guide class return false.")  # debug
    else:
        ndx += 1
    return
