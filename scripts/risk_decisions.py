import _thread
from datetime import datetime

import carla
import time
import pedestrian
import vehicle

DRIVER_VEHICLE = "carlacola"
DETECT_DISTANCE = 100

class risk:

    def __init__(self, location=None):
        self.orientation = '0'
        self.location = carla.Location(x=0, y=0, z=0) if not location else location
        self.vehicle = None
        self.pedestrian = None
        self.control = None
        self.run = False
        self.end =None
        self.driver_distance = 0

    def add_vehicle(self, world, control):
        sp = carla.Transform(self.location, carla.Rotation(pitch=0, yaw=0.0001, roll=0))
        world.wait_for_tick()
        self.vehicle = vehicle.spawn_vehicle(world, spawn_point=sp)
        self.control = carla.VehicleControl() if not control else control

    def start_vehicle(self):
        self.vehicle.apply_control(self.control)
        # self.timestamp = datetime.now().strftime('%H:%M:%S')

    def destroy_vehicle(self, client):
        self.vehicle.destroy()

    def add_pedestrian(self, world, control):
        sp = carla.Transform(self.location, carla.Rotation(pitch=0, yaw=0.0001, roll=0))
        world.wait_for_tick()
        self.pedestrian = pedestrian.spawn_pedestrian(world, sp)
        self.control = carla.WalkerControl() if not control else control

    def start_pedestrian(self):
        self.pedestrian.apply_control(self.control)

    def destroy_pedestrian(self, client):
        self.pedestrian.destroy()


def start_risk(risk):
    if risk.pedestrian:
        risk.start_pedestrian()
    if risk.vehicle:
        risk.start_vehicle()
    return datetime.now()


def stop_risk(risk):
    if risk.pedestrian:
        risk.destroy_pedestrian()
    if risk.vehicle:
        risk.destroy_vehicle()
    risk.run = True
    return datetime.now()


def time_elapsed(start, end):
    return start - end


def autostart(risk, driver, distance_trigger):
    if int(distance_from_driver(driver, risk)) <= distance_trigger:
        start = start_risk(risk)



def distance_from_driver(driver, risk):
    driver_loc = driver.get_location()
    return risk.location.distance(driver_loc)


def get_driver():
    global world
    actors = world.get_actors()
    for actor in actors:
        if actor.id.endswith(DRIVER_VEHICLE):
            return actor




def init():
    client = carla.Client('127.0.0.1', 2000)
    world = client.get_world()
    return world
