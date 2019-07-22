import carla
import random
import time


walkers_list = []


def _init():
    client = carla.Client('127.0.0.1', 2000)
    world = client.get_world()
    return world


def spawn_pedestrian(world, spawn_point=None):
    blueprints = world.get_blueprint_library().filter("walker")
    bp = random.choice(blueprints)
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
    control = control_pedestrian(pedestrian, speed=1, x=1, y=0, z=0, jump=1)
    while True:
        pedestrian.apply_control(control)
        time.sleep(1)


if __name__ == '__main__':
    test()

