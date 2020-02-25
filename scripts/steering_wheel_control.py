#!/usr/bin/env python

# Copyright (c) 2019 Intel Labs
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Allows controlling a vehicle with a keyboard. For a simpler and more
# documented example, please take a look at tutorial.py.

# ==============================================================================
# University of Texas at San Antonio
#
#   Author: Kevin Barba and UAB
#
#   Changes made to the original version:
#       -Change the camera view for the driver
#       -Default to one spawn point (at line 172)
#       -Default to one vehicle blueprint. audi tt (at line )
#       -Modified on-screen information
#       -Uses mph instead of km/h (by just doing the proper conversion)
#       -Create a mode to create logs with the information given, not all
#         of it used. Currently logs are created each second ( to be modified)
#         and exported to logs directory with default name drive.csv
#       -Others
#
#
# ==============================================================================

"""
Welcome to CARLA driving simulator.
Instructions:
    Use steering wheel to change the direction
    Use gas pedal (right pedal) to accelerate
    Use brake pedal (left pedal) to stop
    Use [left paddle] in steering wheel to enable/disable reverse
    Use [R2] button in steering wheel to advance to the next task
    (need to be at the end position)
    Use [L2] button to restart the current task
    Use [option] button to display this screen

    1. Press GAS Pedal
    2. Press Brake Pedal
    3. Press [option] button to start driving

"""

from __future__ import print_function

# ==============================================================================
# -- find carla module ---------------------------------------------------------
# ==============================================================================
import _thread
import datetime
import signal
import task_guide
import thread
import glob
import os
import sys
import stat
import time

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
    sys.path.append('../scripts')
    sys.path.append('../examples')
except IndexError:
    pass


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

from sensors import CollisionSensor, LaneInvasionSensor, GnssSensor
from controllers import DualControl
from text import FadingText, HelpText
from graphic_controls import CameraManager, HUD
import carla
import gps_map
from carla_exception import *
import start_driving
import risk_decisions
import logging
import random
import re
if sys.version_info >= (3, 0):
    from configparser import ConfigParser
else:
    from ConfigParser import RawConfigParser as ConfigParser

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_0
    from pygame.locals import K_9
    from pygame.locals import K_BACKQUOTE
    from pygame.locals import K_BACKSPACE
    from pygame.locals import K_COMMA
    from pygame.locals import K_DOWN
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_F1
    from pygame.locals import K_LEFT
    from pygame.locals import K_PERIOD
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SLASH
    from pygame.locals import K_SPACE
    from pygame.locals import K_TAB
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_c
    from pygame.locals import K_d
    from pygame.locals import K_h
    from pygame.locals import K_m
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_r
    from pygame.locals import K_s
    from pygame.locals import K_w
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')


# ==============================================================================
# -- Global vars  --------------------------------------------------------------
# ==============================================================================
speed = 0
# final_loc = carla.Location(x=187, y=55)


# ==============================================================================
# -- World ---------------------------------------------------------------------
# ==============================================================================


class World(object):
    def __init__(self, carla_world, hud, actor_filter):
        self.world = carla_world
        self.hud = hud
        self.player = None
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.gnss_sensor = None
        self.camera_manager = None
        self._weather_presets = find_weather_presets()
        self._weather_index = 0
        self._actor_filter = actor_filter
        self.restart()
        self.world.on_tick(hud.on_world_tick)

    def restart(self):
        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        # Get a random blueprint.
        blueprint = self.world.get_blueprint_library().filter(self._actor_filter)[1]
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        # Spawn the player.
        if self.player is not None:
            spawn_point = self.player.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            actor = self.world.try_spawn_actor(blueprint, spawn_point)
        while self.player is None:
            spawn_points = self.world.get_map().get_spawn_points()
            spawn_point = spawn_points[123] if spawn_points else carla.Transform()
            # spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        # Set up the sensors.
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.gnss_sensor = GnssSensor(self.player)
        self.camera_manager = CameraManager(self.player, self.hud)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % preset[1])
        self.player.get_world().set_weather(preset[0])

    def tick(self, clock):
        self.hud.tick(self, clock)

    def render(self, display):
        self.camera_manager.render(display)
        self.hud.render(display)

    def destroy(self):
        actors = [
            self.camera_manager.sensor,
            self.collision_sensor.sensor,
            self.lane_invasion_sensor.sensor,
            self.gnss_sensor.sensor,
            self.player]
        for actor in actors:
            if actor is not None:
                actor.destroy()


def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]

# ==============================================================================
# ------Main loop---------------------------------------------------------------
# ==============================================================================


def game_loop(args, clock):
    global hud, controller
    # attack_performed = 0
    pygame.init()
    pygame.font.init()
    world = None

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(2.0)     # timeout in case the client loses connection

        log = create_logfile(args)
        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        hud = HUD(args, log, __doc__)
        world = World(client.get_world(), hud, args.filter)
        controller = DualControl(world, args)
        if args.cyberattack:
            thread.start_new_thread(controller.attack_trigger, ())
        time.sleep(1.5)
        thread.start_new_thread(hud.write_driving_data, (True,))
        while True:
            clock.tick_busy_loop(40)    # max fps in client
            if controller.parse_events(world, clock):
                return
            world.tick(clock)
            world.render(display)
            pygame.display.flip()

    finally:
        time.sleep(1)       # delay to allow threads to finish first
        if world is not None:
            world.destroy()

        pygame.quit()


# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================


def start(args, clock):
    global data_interval

    data_interval = args.data_interval
    args.width, args.height = [int(x) for x in args.res.split('x')]

    if args.debug:
        print(__doc__)
    try:
        # if args.tasklevel == 2:
        #     # args.walkers = 20   # for testing purposes
        #     #     # args.number_of_vehicles = 50
        #     start_driving.main(False, args, args.username)
        # elif args.tasklevel == 3:
        #     # args.walkers = 0  # for testing purposes
        #     # args.number_of_vehicles = 0
        #     args.cyberattack = True
        #     start_driving.main(False, args, args.username)
        #     time.sleep(3)
        #     _thread.start_new_thread(risk_decisions.init, (args.cyberattack,))
        # elif args.tasklevel == 1:
        _thread.start_new_thread(task_guide.main, (args,))
        if args.cyberattack:
            _thread.start_new_thread(risk_decisions.init, (args.cyberattack,))
        elif args.risk:
            _thread.start_new_thread(risk_decisions.init, (False,))

        game_loop(args, clock)
        # else:
        #     raise(Exception("[Error] Task level does not exists"))
    except RestartTask:
        print('________________________________________________________'
              '________________________________________________________')
        print("Restarting task")
        # if child != 0:
        #     os.kill(int(child), signal.SIGKILL)
        game_loop(args, clock)
    # except NextTask:
    #     print('________________________________________________________'
    #           '________________________________________________________')
    #     # args.walkers = 20   # for testing purposes
    #     # args.number_of_vehicles = 50
    #     args.tasklevel = 2
    #     print("Map PID     " + str(start_driving.child))
    #     # if child != 0:
    #     #     os.kill(int(child), signal.SIGKILL)
    #     start_driving.main(False, args, args.username)
    # except LastTask:
    #     print('________________________________________________________'
    #           '________________________________________________________')
    #     # if child != 0:
    #     #     os.kill(int(child), signal.SIGKILL)
    #     start_driving.destroy_NPC(args)
    #     args.walkers = 0  # for testing purposes
    #     args.number_of_vehicles = 0
    #     args.tasklevel = 3
    #     args.cyberattack = True
    #     start_driving.main(False, args, args.username)
    #     time.sleep(3)
    #     _thread.start_new_thread(risk_decisions.init, (args.cyberattack,))
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


def create_logfile(args):
    global attack
    if not os.path.isdir(args.log_filepath):
        # @todo Create custom exception
        raise Exception("log filepath " + args.log_filepath + " does not exists.")
    dir_permission = os.stat(args.log_filepath)
    if not bool(dir_permission.st_mode & stat.S_IWUSR):
        # @todo Create custom exception
        raise Exception("log filepath: " + args.log_filepath + " has not write permission. Try with sudo.")
    logname = _format_logname(args)
    log = open(args.log_filepath + logname, 'w')
    log.write('50ms,Time,Speed,Heading,Location,Throttle,Steer,Brake,Reverse,' +
                  'Near Vehicles,Over Speed,Sign,Stopped,maxRPM,Notifications')
    if args.cyberattack:
        log.write(',Actuator,Delta,Repetitions,Kvalues,Ended,Restablished\n')
    else:
        log.write('\n')
    return log


def _format_logname(args):
    time_now = str(datetime.datetime.now()).replace(' ', '-')
    time_now = time_now[:time_now.index('.')]       # delete anything beyond seconds
    time_now = time_now.replace(':', '')[5:]        # remove year from log
    if args.cyberattack:
        return str(args.username) + '_' + str(time_now) + "a.csv"
    else:
        return str(args.username) + '_' + str(time_now) + ".csv"
    # return str(args.username) + ".csv"
