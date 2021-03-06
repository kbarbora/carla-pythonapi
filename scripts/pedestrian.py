####################################
#University of Texas at San Antonio
#
# Author: Kevin Barba
#
####################################

"""
Models a pedestrians in the driving simulation and functions

Functions to model a pedestrian in carla. Since pedestrian is
already defined by Carla in C++ code, this file does create a
pedestrian class, instead models and perform the functions need it
to configure, spawn and destroy pedestrians. Since in every instance
of a driving simulation includes several pedestrians (100+), where if I
create a class, I have to hold a instance of the world (memory waste) in
order to spawn them for each one.
"""



import carla
import random
import time


walkers_list = []


def _init():
    client = carla.Client('127.0.0.1', 2000)
    world = client.get_world()
    return world


def setup_pedestrian(world, spawn_point=None):
    blueprints = world.get_blueprint_library().filter("walker")
    bp = random.choice(blueprints)
    transform = world.get_map().get_spawn_points()[0] if not spawn_point else spawn_point
    return bp, transform


def spawn_pedestrian(world, spawn_point=None):
    blueprints = world.get_blueprint_library().filter("walker")
    bp = random.choice(blueprints)
    if bp.has_attribute('is_invincible'):
        bp.set_attribute('is_invincible', 'false')
    transform = world.get_map().get_spawn_points()[0] if not spawn_point else spawn_point
    pedestrian = world.spawn_actor(bp, transform)
    return pedestrian


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


def control_pedestrian(pedestrian, speed=1, x=0, y=0, z=0, jump=0):
    control = carla.WalkerControl()
    control.speed = speed
    control.direction.x = x
    control.direction.y = y
    control.direction.z = z
    return control


def modify_control(control, x=None, y=None, z=None, speed=None):
    if (not x) and (not y) and (not z) and (not speed):
        return control
    else:
        if x:
            control.direction.x = x
        if y:
            control.direction.y = y
        if z:
            control.direction.z = z 
        if speed:
            control.speed = speed
        return control


def retrieve_ids(pedestrians_list):
    all_id = []
    for i in range(len(pedestrians_list)):
        all_id.append(pedestrians_list[i]['con'])
        all_id.append(pedestrians_list[i]['id'])
    return all_id


def retrieve_actors(world, all_id):
    return world.get_actors(all_id)


def destroy_pedestrians(client, all_actors, all_id):
    for i in range(0, len(all_id), 2):
        all_actors[i].stop()

    # destroy pedestrian (actor and controller)
    client.apply_batch([carla.command.DestroyActor(x) for x in all_id])


def test():
    world = _init()
    pedestrian = spawn_pedestrian(world)
    control = control_pedestrian(pedestrian, speed=2, x=0, y=1, z=0, jump=0)
    while True:
        pedestrian.apply_control(control)
        time.sleep(1)


if __name__ == '__main__':
    test()

