import argparse
import logging
import os
import stat
import datetime
import glob
import sys
import random
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla


def init(host, port):

    client = carla.Client(host, port)
    client.set_timeout(2.0)

    try:
        world = client.get_world()
        blueprintsWalkers = world.get_blueprint_library().filter("walker.pedestrian.*")
    except Exception:
        raise("An exception ocurred while retrieving the world")
    print("Init successful!")
    return client, world, blueprintsWalkers


def spawn_pedestrians(client, world, blueprintsWalkers, num_pedestrians):
    spawn_points = []
    pedestrians_list = []
    for i in range(num_pedestrians):
        spawn_point = carla.Transform()
        spawn_point.location = world.get_random_location_from_navigation()
        if not spawn_point.location:
            spawn_points.append(spawn_point)
    batch = []
    for spawn_point in spawn_points:
        pedestrian_bp = random.choice(blueprintsWalkers)
        batch.append(carla.command.SpawnActor(pedestrian_bp, spawn_point))

    # apply the batch
    results = client.apply_batch_sync(batch, True)
    print('results is %d' % len(results))
    for i in range(len(results)):
        if results[i].error:
            logging.error(results[i].error)
        else:
            pedestrians_list.append({"id": results[i].actor_id})
    return pedestrians_list


def controller_pedestrian(client, world, pedestrians_list):
    batch = []
    walker_controller_bp = world.get_blueprint_library().find('controller.ai.walker')
    for i in range(len(pedestrians_list)):
        batch.append(carla.command.SpawnActor(walker_controller_bp, carla.Transform(), pedestrians_list[i]["id"]))

    # apply the batch
    results = client.apply_batch_sync(batch, True)
    for i in range(len(results)):
        if results[i].error:
            logging.error(results[i].error)
        else:
            pedestrians_list[i]["con"] = results[i].actor_id


def retrieve_ids(pedestrians_list):
    all_id = []
    for i in range(len(pedestrians_list)):
        all_id.append(pedestrians_list[i]['con'])
        all_id.append(pedestrians_list[i]['id'])
    return all_id


def retrieve_actors(world, all_id):
    return world.get_actors(all_id)


def walk_pedestrians(world, all_actors):
    for i in range(0, len(all_actors), 2):
        all_actors[i].start()
        all_actors[i].go_to_location(world.get_random_location_from_navigation())
        all_actors[i].set_max_speed(1 + random.random())


def destroy_pedestrians(client, all_actors, all_id):
    for i in range(0, len(all_id), 2):
        all_actors[i].stop()

    # destroy pedestrian (actor and controller)
    client.apply_batch([carla.command.DestroyActor(x) for x in all_id])


def spawn_pedestrian(blueprints, location):
    bp = random.choice(blueprints)
    carla.commnad.SpawnActor(bp, location)


if __name__ == '__main__':
    try:
        c, w, bp = init('127.0.0.1', 2000)
        ped = spawn_pedestrians(c, w, bp, 10)
        print(ped)
        controller_pedestrian(c, w, ped)
        ids = retrieve_ids(ped)
        actors = retrieve_actors(w, ids)
        w.wait_for_tick()
        walk_pedestrians(w, actors)
        print(actors)
    except(Exception):
        pass
    # finally:
        # destroy_pedestrians()
