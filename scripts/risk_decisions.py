import _thread
from datetime import datetime

import carla
import time
import pedestrian
import vehicle

DRIVER_VEHICLE = "tt"
DETECT_DISTANCE = 100
WAYPOINT_SEPARATION = 4


class risk:
    def __init__(self, world, spawn_point, control=None):
        self.orientation = '0'
        self.world = world
        self.map = world.get_map()
        if isinstance(spawn_point, list):
            self.spawn_point = spawn_point
            self.location = spawn_point[0].location
        else:
            self.spawn_point = spawn_point
            self.location = spawn_point.location
        # self.waypoint = self.map.get_waypoint(location)
        # self.rotation = self.waypoint.transform.rotation.yaw
        self.vehicle_list = []
        self.pedestrian_list = []
        self.control = None if not control else control
        self.run = False
        self.end = None
        self.driver_distance = 0

    # def next_waypoint(self):
    #     self.waypoint = list(self.waypoint.next(WAYPOINT_SEPARATION))[0]
    #     self.rotation = self.waypoint.transform.rotation.yaw

    # def add_spawn_point(self, spawn_point):
    #     if self.spawn_point:
    #         self.spawn_point = [self.spawn_point]
    #         self.spawn_point.append(spawn_point)
    #     else:
    #         self.spawn_point = spawn_point
    #     return

    def add_vehicle(self, spawn_point=0, rotation=0, filter=None):
        # location = self.spawn_point.location
        # if rotation:
        #     rotation = carla.Rotation(pitch=0, yaw=rotation, roll=0)
        print(spawn_point)
        if spawn_point:
            print("Adding vehicle in spawn point choosen")
            sp = self.spawn_point[spawn_point]
        elif isinstance(self.spawn_point, list):
            sp = self.spawn_point[0]
        else:
            sp = self.spawn_point
        #     sp = carla.Transform(location, rotation)
        self.world.wait_for_tick()
        new_vehicle = vehicle.spawn_vehicle(spawn_point=sp, filter=filter)
        time.sleep(.1)
        if new_vehicle:
            self.vehicle_list.append(new_vehicle)
        return new_vehicle.type_id

    # def add_xvehicles(self, x=2, offset=0, rotation=0):
    #     counter = 0
    #     if rotation:
    #         self.rotation = rotation
    #     for v in range(x):
    #         self.add_vehicle(offset, self.rotation)
    #         self.next_waypoint()
    #         counter += 1
    #     return counter

    def start_vehicle(self):
        for v in self.vehicle_list:
            v.set_autopilot(True)
            # v.apply_control(self.control)
        #   self.timestamp = datetime.now().strftime('%H:%M:%S')

    def destroy_vehicle(self):
        for v in self.vehicle_list:
            v.destroy()
        return

    def add_pedestrian(self, control=0):
        sp = carla.Transform(self.spawn_point.location, carla.Rotation(pitch=0, yaw=0.0001, roll=0))
        self.world.wait_for_tick()
        self.pedestrian_list.append(pedestrian.spawn_pedestrian(self.world, sp))
        self.control = carla.WalkerControl() if not control else control
        return

    def start_pedestrian(self):
        world_g.wait_for_tick()
        for ped in self.pedestrian_list:
            ped.apply_control(self.control)
        print("pedestrian activated")
        return

    def destroy_pedestrian(self, client):
        self.pedestrian_list.destroy()
        return


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
    global world_g
    actors = world_g.get_actors()
    print(DRIVER_VEHICLE)
    for actor in actors:
        if actor.type_id.endswith(DRIVER_VEHICLE):
            return actor


def init():
    global world_g, driver_g
    client = carla.Client('127.0.0.1', 2000)
    world_g = client.get_world()
    sp = carla.Map.get_spawn_points(world_g.get_map())
    counter = 0
    ri = risk(world_g, spawn_point=sp[10])
    risks = [ri]
    driver_g = get_driver()
    started = True
    for r in risks:
        # risk_bike_crossing(r)
        # risk_carlacola(r)
        # risk_tunnel(r)
        risk_ped_park(r)
        # print(control)
        # r.add_pedestrian(control=control)
        # while started:
        #
        #     dist = distance_from_driver(driver_g, r)
        #     print(dist)
        #     time.sleep(.1)
        #     if int(dist) < 60:
        #         print('YESSS')
        #         r.start_pedestrian()
        #         started = False
        #         time.sleep(5)
        # finally:
        #     r.destroy_vehicle()


def risk_ped_park(r, threshold=40):
    control = carla.WalkerControl()
    control.speed = 3
    control.direction.x = 0
    control.direction.y = 1
    r.add_pedestrian(control=control)
    while True:
        dist = distance_from_driver(driver_g, r)
        print(dist)
        time.sleep(.1)
        if int(dist) < threshold:
            print("----------Pedestrian in park activated")
            r.start_pedestrian()
            time.sleep(2)
            r.add_pedestrian(control=control)
            r.start_pedestrian()
            return



def risk_tunnel(r, threshold=80):
    r.add_vehicle(filter='toyota*')
    r.add_vehicle(spawn_point=1, filter='volk*')
    while True:
        time.sleep(.1)
        dist = distance_from_driver(driver_g, r)
        print(dist)
        if int(dist) < threshold:
            print('-------------Tunnel risk activated')
            r.start_vehicle()
            return True


def risk_carlacola(r, threshold=80):
    print(r.add_vehicle(filter='jeep*'))
    while True:
        time.sleep(.1)
        dist = distance_from_driver(driver_g, r)
        print(dist)
        if int(driver_g.get_location().y) < threshold:
            print('--------------CarlaCola risk activated')
            r.start_vehicle()
            return True


def risk_bike_crossing(r, threshold=55):
    r.add_vehicle(filter='bh*')
    while True:
        time.sleep(.1)
        dist = distance_from_driver(driver_g, r)
        print(dist)
        if int(dist) <= threshold:
            r.start_vehicle()
            return True


# def main():


if __name__ == '__main__':
    init()
