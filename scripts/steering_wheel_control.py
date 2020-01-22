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


"""

from __future__ import print_function

# ==============================================================================
# -- find carla module ---------------------------------------------------------
# ==============================================================================
import _thread

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
from carla import ColorConverter as cc
import collections
import datetime
import logging
import math
import random
import re
import weakref
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
    global hud, log, k_values, attack

    k_values = [1.0, 1.6, 1.6]
    # attack_performed = 0
    if attack:
        attack['interval'] = attack['values'][4]
        attack['inital'] = attack['values'][5]
        attack['restablished'] = attack['values'][6]
        attack['repetitions'] = attack['values'][7]

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

        hud = HUD(args.width, args.height, log, __doc__)
        world = World(client.get_world(), hud, args.filter)
        if attack:
            controller = DualControl(world, args.autopilot, attack, args.tasklevel)
            thread.start_new_thread(controller.attack_counter, ())
        else:
            controller = DualControl(world, args.autopilot, None, args.tasklevel)
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


def start(args, clock, attack_values):
    global attack, data_interval, freq_data

    data_interval = args.data_interval
    freq_data = 1 / data_interval
    if attack_values:
        attack = {'values': attack_values}
    else:
        attack = None
    args.width, args.height = [int(x) for x in args.res.split('x')]

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)
    try:
        game_loop(args, clock)
    except RestartTask:
        print('________________________________________________________'
              '________________________________________________________')
        print("Restarting task")
        game_loop(args, clock)
    except NextTask:
        print('________________________________________________________'
              '________________________________________________________')
        args.walkers = 20   # for testing purposes
        args.number_of_vehicles = 50
        args.tasklevel = 1
        start_driving.main(False, args)
    except LastTask:
        print('________________________________________________________'
              '________________________________________________________')
        start_driving.destroy_NPC(args)
        args.walkers = 0  # for testing purposes
        args.number_of_vehicles = 0
        args.tasklevel = 2
        _thread.start_new_thread(risk_decisions.init, ())
        start_driving.main(False, args)
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


def create_logfile(args):
    global log
    if not os.path.isdir(args.log_filepath):
        # @todo Create custom exception
        raise Exception("log filepath " + args.log_filepath + " does not exists.")
    dir_permission = os.stat(args.log_filepath)
    if not bool(dir_permission.st_mode & stat.S_IWUSR):
        # @todo Create custom exception
        raise Exception("log filepath: " + args.log_filepath + " has not write permission. Try with sudo.")
    logname = format_logname(args)
    log = open(args.log_filepath + logname, 'w')
    log.write('Seconds,Speed,Heading,Location,Throttle,Steer,Brake,Reverse,' +
              'Near Vehicles,Over SL,' +
              'Red Light,Stopped RL,Notifications\n')
    # log.write('Seconds,Speed,Heading,Location,Throttle,Steer,Brake,Reverse,' +
    #           'Near Vehicles,Over SL,' +
    #           'Red Light,Stopped RL,Max RPM, MoI, DRFT, DRZTCE, DRZTCD, Final Ratio,' +
    #           'Mass,Drag,MassCenter,Notifications\n')
    return log


def format_logname(args):
    # time_now = str(datetime.datetime.now()).replace(' ', '-')
    # time_now = time_now[:time_now.index('.')]       # delete anything beyond seconds
    # time_now = time_now.replace(':', '')
    # return str(args.username) + '_' + str(time_now) + ".log"
    return "driver.csv"  # @todo Placeholder for debug purposes
