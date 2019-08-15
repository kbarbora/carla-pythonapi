import _thread
from datetime import datetime

import carla
import time
import pedestrian
import vehicle

DRIVER_VEHICLE = "carlacola"
DETECT_DISTANCE = 100

class risk:

    def __init__(self, world, location, control=None):
        self.orientation = '0'
        self.world = world
        self.location = location
        self.vehicle = []
        self.pedestrian = []
        self.control = None if not control else control
        self.run = False
        self.end =None
        self.driver_distance = 0

    def add_spawn_point(self, spawn_point):
        if self.spawn_point:
            self.spawn_point = [self.spawn_point]
            self.spawn_point.append(spawn_point)
        else:
            self.spawn_point = spawn_point
        return

    def add_vehicle(self, offset, rotation, autopilot=False):
        rotation = carla.Rotation(pitch=0, yaw=rotation, roll=0)
        if offset:
            offset_location = self.location
            offset_location.x += offset[0]
            offset_location.y += offset[1]
            offset_location.z += offset[2]
            sp = carla.Transform(offset_location, rotation)
        else:
            sp = carla.Transform(self.location, rotation)
        self.world.wait_for_tick()
        self.vehicle.append(vehicle.spawn_vehicle(self.world, spawn_point=sp))
        self.vehicle[-1].set_autopilot(autopilot)
        return

    def start_vehicle(self):
        for v in self.vehicle:
            v.apply_control(self.control)
        #   self.timestamp = datetime.now().strftime('%H:%M:%S')

    def start_autopilot_vehicle(self):

        self.vehicle.apply_control(self.control)
        # self.timestamp = datetime.now().strftime('%H:%M:%S')

    def destroy_vehicle(self):
        for v in self.vehicle:
            v.destroy()

    def add_pedestrian(self, control):
        sp = carla.Transform(self.location, carla.Rotation(pitch=0, yaw=0.0001, roll=0))
        self.world.wait_for_tick()
        self.pedestrian = pedestrian.spawn_pedestrian(self.world, sp)
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
    risks = []
    risks.append(risk(world, carla.Location(x=-87, y=-162, z=10)))
    try:
        for r in risks:
            r.add_vehicle(0, 90, False)
            r.add_vehicle((-1, -5, 0), 90, False)
            r.add_vehicle((-1, -10, 0), 90, False)
            r.add_vehicle((-1, -15, 0), 90, False)
            r.add_vehicle((-1, -20, 0), 90, False)
        time.sleep(10)
    finally:
        r.destroy_vehicle()


# def main():

if __name__ == '__main__':
    init()