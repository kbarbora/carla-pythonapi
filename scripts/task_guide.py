#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# ==============================================================================
# University of Texas at San Antonio
#
#   Author: Kevin Barba and UAB
# ==============================================================================

"""
Defines the route that the driver is supposed to follow.

Defines the route that the driver is going to be following and utility
functions to do so.
"""

import glob
import os
import random
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import pygame
import argparse
import math
import time

GREEN = carla.Color(100, 255, 0)
BLUE = carla.Color(0, 0, 255)
TICK_TIME = .5
WP_SEP = 4
LIFETIME = 430
DRIVER_VEHICLE = "tt"
RARROW = pygame.image.load('../media/images/arrow_right.png')
LARROW = pygame.image.load('../media/images/arrow_left.png')


def get_driver(world):
    actors = world.get_actors()
    # print(DRIVER_VEHICLE)
    print("trying to get driver")
    for actor in actors:
        if actor.type_id.endswith(DRIVER_VEHICLE):
            print("driver FOUND")
            return actor

def go_straight(debug, current, steps=1):
    for i in range(0, steps):
        # print(list(current.next(WP_SEP)))
        next_w = list(current.next(WP_SEP))[0]
        draw_waypoint_union(debug, current, next_w, GREEN, LIFETIME)

        # update the current waypoint and sleep for some time
        current = next_w
        time.sleep(TICK_TIME)
    return current


def change_lane(debug, current):
    right_lane = current.get_right_lane()
    change = right_lane.next(WP_SEP)
    draw_waypoint_union(debug, current, change[0], GREEN, LIFETIME)
    return list(right_lane.next(WP_SEP))[0]


def make_left(debug, current, step=4):
    for i in range(0, step):
        potential = list(current.next(WP_SEP))
        if len(potential) > 1:
            next_w = potential[-2]
        else:
            next_w = potential[-1]
        draw_waypoint_union(debug, current, next_w, GREEN, LIFETIME)

        # update the current waypoint and sleep for some time
        current = next_w
        time.sleep(TICK_TIME)
    return current


def make_right(debug, current, step=4):
    for i in range(0, step):
        next_w = list(current.next(WP_SEP))[-1]
        draw_waypoint_union(debug, current, next_w, GREEN, LIFETIME)

        # update the current waypoint and sleep for some time
        current = next_w
        time.sleep(TICK_TIME)
    return current


def draw_transform(debug, trans, col=carla.Color(255, 0, 0), lt=-1):
    yaw_in_rad = math.radians(trans.rotation.yaw)
    pitch_in_rad = math.radians(trans.rotation.pitch)
    p1 = carla.Location(
        x=trans.location.x + math.cos(pitch_in_rad) * math.cos(yaw_in_rad),
        y=trans.location.y + math.cos(pitch_in_rad) * math.sin(yaw_in_rad),
        z=trans.location.z + math.sin(pitch_in_rad))
    # debug.draw_arrow(trans.location, p1, thickness=0.05, arrow_size=1.0, color=col, life_time=lt)


def draw_waypoint_union(debug, w0, w1, color=carla.Color(255, 0, 0), lt=-1):
    debug.draw_line(
        w0.transform.location + carla.Location(z=0.25),
        w1.transform.location + carla.Location(z=0.25),
        thickness=0.1, color=color, life_time=lt, persistent_lines=False)
    # debug.draw_point(w1.transform.location + carla.Location(z=0.25), 0.1, color, lt, True)


def draw_waypoint_info(debug, w, lt=5):
    w_loc = w.transform.location
    debug.draw_string(w_loc + carla.Location(z=0.5), "lane: " + str(w.lane_id), False, lt=lt)
    debug.draw_string(w_loc + carla.Location(z=1.0), "road: " + str(w.road_id), False, lt=lt)
    debug.draw_string(w_loc + carla.Location(z=-.5), str(w.lane_change), False, lt=lt)


def draw_arrow(debug, current):
    loc = current.transform.location
    debug.draw_line(
        loc + carla.Location(z=0.25),
        loc + carla.Location(y=-10, z=0.25),
        thickness=0.1, color=GREEN, life_time=LIFETIME, persistent_lines=False)


def main(args=None):
    # argparser = argparse.ArgumentParser()
    # argparser.add_argument(
    #     '--host',
    #     metavar='H',
    #     default='127.0.0.1',
    #     help='IP of the host server (default: 127.0.0.1)')
    # argparser.add_argument(
    #     '-p', '--port',
    #     metavar='P',
    #     default=2000,
    #     type=int,
    #     help='TCP port to listen to (default: 2000)')
    # argparser.add_argument(
    #     '-x',
    #     default=70.0,
    #     type=float,
    #     help='X start position (default: 0.0)')
    # argparser.add_argument(
    #     '-y',
    #     default=8.0,
    #     type=float,
    #     help='Y start position (default: 0.0)')
    # argparser.add_argument(
    #     '-z',
    #     default=0.0,
    #     type=float,
    #     help='Z start position (default: 0.0)')
    # argparser.add_argument(
    #     '-s', '--seed',
    #     metavar='S',
    #     default=os.getpid(),
    #     type=int,
    #     help='Seed for the random path (default: program pid)')
    # argparser.add_argument(
    #     '-t', '--tick-time',
    #     metavar='T',
    #     default=0.2,
    #     type=float,
    #     help='Tick time between updates (forward velocity) (default: 0.2)')
    # args = argparser.parse_args()

    # TICK_TIME = args.TICK_TIME
    try:
        client = carla.Client('127.0.0.1', 2000)
        client.set_timeout(2.0)

        world = client.get_world()
        m = world.get_map()
        debug = world.debug

        random.seed(24371)
        # random.seed(args.seed)

        loc = carla.Location(70.0, 8.0, 0)
        print("Initial location: ", loc)    # debug

        current = m.get_waypoint(loc)
        # print(current)
        counter = 0
        # main loop
        time.sleep(5)
        current = go_straight(debug, current, 137)
        current = make_right(debug, current)
        current = go_straight(debug, current, 10)
        current = make_right(debug, current)
        current = go_straight(debug, current, 50)
        current = make_left(debug, current)
        current = go_straight(debug, current, 70)
        current = make_right(debug, current, 7)
        current = go_straight(debug, current, 115)
        current = make_right(debug, current, 5)
        current = go_straight(debug, current, 10)
        current = make_right(debug, current)
        current = go_straight(debug, current, 15)
        current = make_right(debug, current)
        current = go_straight(debug, current, 13)
        current = make_right(debug, current, 5)
        current = go_straight(debug, current, 10)
        current = make_right(debug, current, 5)
        current = go_straight(debug, current, 78)
        current = make_left(debug, current, 6)
        current = go_straight(debug, current, 10)
        current = change_lane(debug, current)
        current = go_straight(debug, current, 12)
        current = make_right(debug, current, 10)
        current = go_straight(debug, current, 21)
        current = change_lane(debug, current)
        current = make_right(debug, current)
        current = go_straight(debug, current, 21)
        current = make_right(debug, current)
        current = go_straight(debug, current, 40)
        current = make_right(debug, current, 6)
        current = go_straight(debug, current, 115)
        current = change_lane(debug, current)
        current = go_straight(debug, current, 15)
        current = make_right(debug, current)
        current = go_straight(debug, current, 11)
        current = make_right(debug, current, 6)
        current = go_straight(debug, current, 8)
        current = change_lane(debug, current)
        debug.draw_line(
            current.transform.location + carla.Location(z=0.25),
            current.transform.location + carla.Location(y=-10, z=0.25),
            thickness=0.1, color=GREEN, life_time=LIFETIME, persistent_lines=False)
        # current = go_straight(debug, current, 3)

    finally:
        pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nExit by user.')
    finally:
        print('\nExit.')
