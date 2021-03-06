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

"""Spawn NPCs into the simulation

Spawn NPCs into the simulation, when spawn with the command line argument
"""

import glob
import os
import sys
import time

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import logging
import random


def main(args, vehicles_list, walkers_list, all_id):

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    # vehicles_list = []
    # walkers_list = []
    # all_id = []
    client = carla.Client(args.host, args.port)
    client.set_timeout(2.0)

    world = client.get_world()
    blueprints = world.get_blueprint_library().filter(args.filterv)
    blueprintsWalkers = world.get_blueprint_library().filter(args.filterw)
    blueprints = [x for x in blueprints if not x.id.endswith('carlacola')]

    if args.safe:
        blueprints = [x for x in blueprints if int(x.get_attribute('number_of_wheels')) == 4]
        blueprints = [x for x in blueprints if not x.id.endswith('isetta')]
        blueprints = [x for x in blueprints if not x.id.endswith('carlacola')]

    spawn_points = world.get_map().get_spawn_points()
    risk_sp = [123, 25, 24, 23, 22, 21, 20, 19, 16, 15, 13, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    for i in risk_sp:
        spawn_points.remove(spawn_points[i])  # remove initial spawn point for the actual driver ans risks
    number_of_spawn_points = len(spawn_points)

    if args.number_of_vehicles < number_of_spawn_points:
        random.shuffle(spawn_points)
    elif args.number_of_vehicles > number_of_spawn_points:
        msg = 'requested %d vehicles, but could only find %d spawn points'
        logging.warning(msg, args.number_of_vehicles, number_of_spawn_points)
        args.number_of_vehicles = number_of_spawn_points

    # @todo cannot import these directly.
    SpawnActor = carla.command.SpawnActor
    SetAutopilot = carla.command.SetAutopilot
    FutureActor = carla.command.FutureActor

    # --------------
    # Spawn vehicles
    # --------------
    batch = []
    for n, transform in enumerate(spawn_points):
        if n >= args.number_of_vehicles:
            break
        blueprint = random.choice(blueprints)
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        if blueprint.has_attribute('driver_id'):
            driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
            blueprint.set_attribute('driver_id', driver_id)
        blueprint.set_attribute('role_name', 'autopilot')
        batch.append(SpawnActor(blueprint, transform).then(SetAutopilot(FutureActor, True)))

    for response in client.apply_batch_sync(batch):
        if response.error:
            logging.error(response.error)
        else:
            vehicles_list.append(response.actor_id)

    # -------------
    # Spawn Walkers
    # -------------
    # 1. take all the random locations to spawn
    spawn_points = []
    for i in range(args.walkers):
        spawn_point = carla.Transform()
        loc = world.get_random_location_from_navigation()
        if (loc != None):
            spawn_point.location = loc
            spawn_points.append(spawn_point)
    # 2. we spawn the walker object
    batch = []
    for spawn_point in spawn_points:
        walker_bp = random.choice(blueprintsWalkers)
        # set as not invencible
        if walker_bp.has_attribute('is_invincible'):
            walker_bp.set_attribute('is_invincible', 'false')
        time.sleep(.1)  # Delay for spawning pedestrians
        batch.append(SpawnActor(walker_bp, spawn_point))
    results = client.apply_batch_sync(batch, True)
    for i in range(len(results)):
        if results[i].error:
            logging.error(results[i].error)
        else:
            walkers_list.append({"id": results[i].actor_id})
    # 3. we spawn the walker controller
    batch = []
    walker_controller_bp = world.get_blueprint_library().find('controller.ai.walker')
    for i in range(len(walkers_list)):
        batch.append(SpawnActor(walker_controller_bp, carla.Transform(), walkers_list[i]["id"]))
    results = client.apply_batch_sync(batch, True)
    for i in range(len(results)):
        if results[i].error:
            logging.error(results[i].error)
        else:
            walkers_list[i]["con"] = results[i].actor_id
    # 4. we put altogether the walkers and controllers id to get the objects from their id
    for i in range(len(walkers_list)):
        all_id.append(walkers_list[i]["con"])
        all_id.append(walkers_list[i]["id"])
    all_actors = world.get_actors(all_id)

    # wait for a tick to ensure client receives the last transform of the walkers we have just created
    world.wait_for_tick()

    # 5. initialize each controller and set target to walk to (list is [controler, actor, controller, actor ...])
    for i in range(0, len(all_id), 2):
        # start walker
        all_actors[i].start()
        # set walk to random point
        all_actors[i].go_to_location(world.get_random_location_from_navigation())
        # random max speed
        all_actors[i].set_max_speed(1 + random.random())    # max speed between 1 and 2 (default is 1.4 m/s)

    print('spawned %d vehicles and %d walkers, press Ctrl+C to exit.' % (len(vehicles_list), len(walkers_list)))

    while True:
        world.wait_for_tick()


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')
