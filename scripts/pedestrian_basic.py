# ==============================================================================
# University of Texas at San Antonio
#
#   Author: Kevin Barba
# ==============================================================================

"""
Blueprint to implement the pedestrians
"""

import carla
import random
import time


walkers_list = []
client = carla.Client('127.0.0.1', 2000)
world = client.get_world()
blueprints = world.get_blueprint_library().filter("walker")

bp = random.choice(blueprints)
transform = world.get_map().get_spawn_points()[0]
transform.location.x = -5
print(transform)
pedestrian = world.spawn_actor(bp, transform)
while True:
    control = carla.WalkerControl()
    control.speed = 1
    control.direction.x = 1
    control.direction.y = 0
    control.direction.z = 0
    pedestrian.apply_control(control)
    time.sleep(1)
    control.jump = 1
    pedestrian.apply_control(control)
    time.sleep(1)
