#!/usr/bin/python3
####################################
#University of Texas at San Antonio
#
# Author: Kevin Barba
#
####################################

"""
Defines a game thread to be used in Carla

Currently not in used.
"""
import threading
import time
import sys
sys.path.append('../examples')
from manual_control_steeringwheel import game_loop


_exitFlag = False


class game_thread(threading.Thread):
    def __init__(self, threadName, args):
        threading.Thread.__init__(self)
        self.threadName = threadName
        self.args = args

    def run(self):
        print("Starting " + self.name)
        game_loop(self.args)
        print("Exiting " + self.name)


def stop_thread(threadName):
    if _exitFlag:
        threadName.exit()


def print_time(threadName, delay):
    if _exitFlag:
        threadName.exit()
    time.sleep(delay)
    print("%s: %s" % (threadName, time.ctime(time.time())))


def set_Flag(flag):
    global _exitFlag
    _exitFlag = flag
