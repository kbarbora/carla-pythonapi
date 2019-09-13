# ==============================================================================
# University of Texas at San Antonio
#
#   Author: Kevin Barba
# ==============================================================================

"""
Models a vehicle in the driving simulation and functions

Functions to model a vehicle in carla. Since vehicle is
already defined by Carla in C++ code, this file does create a
vehicle class, instead models and perform the functions need it
to configure, spawn and destroy vehicles. Since in every instance
of a driving simulation includes several vehicles (100+), where if I
create a class, I have to hold a instance of the world (memory waste) in
order to spawn them for each one.
"""

import _thread      # For testing purposes
import carla
import random
import time

vehicle_list = []


def _init():
    global world
    global blueprints
    client = carla.Client('127.0.0.1', 2000)
    world = client.get_world()
    blueprints = world.get_blueprint_library().filter("vehicle")
    # return world


def setup_vehicle(blueprint=None, spawn_point=None):
    global blueprints, world
    bp = random.choice(blueprints) if not blueprint else blueprint
    transform = world.get_map().get_spawn_points()[0] if not spawn_point else spawn_point
    return bp, transform


def spawn_vehicle(filter=None, spawn_point=None):
    global world, blueprints
    _init()
    if not filter:
        blueprint = random.choice(blueprints)
    else:
        print("vehicle." + filter)
        blueprint = world.get_blueprint_library().filter("vehicle." + filter)
        blueprint = blueprint[0]
    transform = world.get_map().get_spawn_points()[0] if not spawn_point else spawn_point
    vehicle = world.spawn_actor(blueprint, transform)
    return vehicle


def modify_spawn_point(spawn_point, x=None, y=None, z=None):
    if (not x) and (not y) and (not z):
        return spawn_point
    else:
        if x:
            spawn_point.x = x
        if y:
            spawn_point.y = y
        if z:
            spawn_point.z = z
        return spawn_point


def modify_control(control, brake=0, gear=0, reverse=False, steer=0, throttle=0):
    if brake:
        control.brake = brake
    if gear:
        control.gear = gear
    if reverse:
        control.reverse = True
    if steer:
        control.steer = steer
    if throttle:
        control.throttle = throttle
    return control


def retrieve_ids(vehicle_list):
    all_id = []
    for i in range(len(vehicle_list)):
        all_id.append(vehicle_list[i]['con'])
        all_id.append(vehicle_list[i]['id'])
    return all_id


def retrieve_actors(world, all_id):
    return world.get_actors(all_id)


def destroy_vehicles(client, all_actors, all_id):
    for i in range(0, len(all_id), 2):
        all_actors[i].stop()

    # destroy vehicle (actor and controller)
    client.apply_batch([carla.command.DestroyActor(x) for x in all_id])


def test():
    world = _init()
    vehicle = spawn_vehicle(world)
    control = carla.VehicleControl()
    control = modify_control(control, throttle=0, steer=-.5)
    _thread.start_new_thread(vehicle_loop, (vehicle, control))
    # while True:
    #     vehicle.apply_control(control)
    #     time.sleep(1)


def vehicle_loop(vehicle, control):
    while True:
        vehicle.apply_control(control)
        time.sleep(1)

if __name__ == '__main__':
    test()

