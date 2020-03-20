# ==============================================================================
# University of Texas at San Antonio
#
#   Author: Kevin Barba
# ==============================================================================

"""Represent situations where the driver has to make a decision.

Within this python file, the risk class is defined. It models
high risk situations where the driver has to make a decision,
and react accordingly. Each risk object contains a instance
of the actual world, the current map, the possible spawn points
and the location of only one of the spawn points, in addition
the vehicles and/or pedestrians that are going to be spawn during
the activation of the risk and there respective controls.
There are functions definingcomplete risk situations
(functions named 'risk...').
"""


import _thread
from datetime import datetime
import carla
import time
import pedestrian
import vehicle

DRIVER_VEHICLE = "tt"
DETECT_DISTANCE = 100
WAYPOINT_SEPARATION = 4
attack = 0


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
        return

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


def autostart(this_risk, driver, distance_trigger):
    if int(_distance_from_driver(driver, this_risk)) <= distance_trigger:
        start = start_risk(this_risk)


def _distance_from_driver(driver, this_risk):
    driver_loc = driver.get_location()
    return this_risk.location.distance(driver_loc)


def _get_driver():
    global world_g
    actors = world_g.get_actors()
    # print(DRIVER_VEHICLE)
    print("trying to get driver")
    for actor in actors:
        if actor.type_id.endswith(DRIVER_VEHICLE):
            print("driver FOUND")
            return actor


def init(cyberattack=False):
    global world_g, driver_g, attack
    print("***starting risks")
    attack = "attack" if cyberattack else 0  # global variable indicating the current attack
    client = carla.Client('127.0.0.1', 2000)
    world_g = client.get_world()
    sp = carla.Map.get_spawn_points(world_g.get_map())
    time.sleep(3)
    bike_crossing = risk(world_g, spawn_point=sp[2])
    carla_cola = risk(world_g, spawn_point=sp[21])
    tunnel = risk(world_g, spawn_point=sp[3:5])
    park = risk(world_g, spawn_point=sp[25])
    # stop = [sp[12], sp[9], sp[5], sp[22], sp[20], sp[23], sp[16]]
    stop = [sp[12], sp[9], sp[22], sp[20], sp[16]]
    stop_traffic = risk(world_g, spawn_point=stop)
    sculpture = risk(world_g, spawn_point=[sp[1], sp[0], sp[24]])
    traffic_jam = risk(world_g, spawn_point=[sp[10], sp[8], sp[6], sp[10], sp[7], sp[15], sp[13], sp[19]])
    risks = [bike_crossing, carla_cola, tunnel, park, stop_traffic, sculpture, traffic_jam]
    time.sleep(10)
    driver_g = _get_driver()
    risk_bike_crossing(risks[0])
    # time.sleep(5)
    risk_carlacola(risks[1])
    risk_tunnel(risks[2])
    risk_ped_park(risks[3])
    risk_no_stop_cars(risks[4])
    risk_front_sculpture(risks[5])
    risk_traffic_jam(risks[6])
    if attack:
        attack = activate_attack(risk(world_g, spawn_point=sp[19]), 'combo', -50)

    started = True
    # for r in risks:
        # risk_bike_crossing(r)
        # time.sleep(5)
        # risk_carlacola(r)
        # risk_tunnel(r)
        # risk_ped_park(r)
        # risk_no_stop_cars(r)
        # risk_front_sculpture(r)
        # risk_traffic_jam(r)
        # for s in range(len(r.spawn_point)):
        #     r.add_vehicle(spawn_point=s)
        #     time.sleep(.1)
        # while started:
        #     dist = distance_from_driver(driver_g, r)
        #     # print(dist)
        #     time.sleep(.1)
        #     if int(dist) < 55:
        #         print('YESSS')
        #         r.start_vehicle()
        #         started = False
        #         sp_index = 0
        #         time.sleep(5)
        #         while True:
        #             dist = distance_from_driver(driver_g, r)
        #             for s in range(len(r.spawn_point)):
        #                 print(s)
        #                 r.add_vehicle(spawn_point=s)
        #                 time.sleep(2)
        #                 r.start_vehicle()
        #             if int(dist) > 80:
        #                 break


def risk_traffic_jam(r, threshold=60):
    # sp 10, 8, 6, 10, 7, 15, 13 and maybe 19
    # sps = [sp[13], sp[6], sp[11], sp[10], sp[8], sp[15], sp[7]]
    for s in range(len(r.spawn_point)):
        r.add_vehicle(spawn_point=s)
        time.sleep(.1)
    while True:
        dist = _distance_from_driver(driver_g, r)
        # print(dist)
        time.sleep(.1)
        if int(dist) < 55:
            print('YESSS')
            r.start_vehicle()
            time.sleep(5)
            while True:
                dist = _distance_from_driver(driver_g, r)
                for s in range(len(r.spawn_point)):
                    # try:
                    r.add_vehicle(spawn_point=s)
                    # except RuntimeError:
                        # return True
                    time.sleep(2.5)
                    r.start_vehicle()
                if int(dist) > threshold:
                    return True


def risk_front_sculpture(r, threshold=45):
    global attack
    # sp 1, 0, 24
    # sps = [sp[1], sp[20], sp[0]]
    for s in range(3):
        print('car added')
        r.add_vehicle(spawn_point=s)
        time.sleep(.1)
    if attack:
        attack = activate_attack(r, "sculpture", 50)
    while True:
        dist = _distance_from_driver(driver_g, r)
        # print(dist)
        time.sleep(.1)
        if int(dist) < threshold:
            print('-----------Front Sculpture activated')
            r.start_vehicle()
            time.sleep(2)
            while True:
                time.sleep(4)
                # try:
                dist = _distance_from_driver(driver_g, r)
                r.add_vehicle(spawn_point=-1)
                r.start_vehicle()
                if int(dist) > threshold+10:
                    return True
                # except RuntimeError:
                #     return True


def risk_no_stop_cars(r, threshold=60):
    global attack
    # sp 22, 5, 9, 12, 16, 23, 20
    # r.spawn_point = [r.spawn_point[12], r.spawn_point[9], r.spawn_point[5], r.spawn_point[16], r.spawn_point[20], r.spawn_point[23], r.spawn_point[22]]
    # mid = [sp[12], sp[14], sp[5], sp[9], sp[19], sp[18], sp[16]]
    for s in range(len(r.spawn_point)):
        r.add_vehicle(spawn_point=s)
        time.sleep(.1)
    if attack:
        attack = activate_attack(r, 'inters', 45)

    while True:
        dist = _distance_from_driver(driver_g, r)
        # print(dist)
        time.sleep(.1)
        if int(dist) < threshold:
            print("----------Non stop cars activated")
            r.start_vehicle()
            return True


def risk_ped_park(r, threshold=43):
    # sp 25
    control = carla.WalkerControl()
    control.speed = 3
    control.direction.x = 0
    control.direction.y = 1
    r.add_pedestrian(control=control)
    while True:
        dist = _distance_from_driver(driver_g, r)
        # print(dist)
        time.sleep(.1)
        if int(dist) < threshold:
            print("----------Pedestrian in park activated")
            r.start_pedestrian()
            time.sleep(2)
            r.add_pedestrian(control=control)
            r.start_pedestrian()
            return True


def risk_tunnel(r, threshold=60):
    global attack
    # sp 3, 4
    r.add_vehicle(filter='toyota*')
    r.add_vehicle(spawn_point=1, filter='volk*')
    if attack:
        attack = activate_attack(r, "tunnel", 80)
    while True:
        time.sleep(.1)
        dist = _distance_from_driver(driver_g, r)
        # print(dist)
        if int(dist) < threshold:
            print('-------------Tunnel risk activated')
            r.start_vehicle()
            return True


def risk_carlacola(r, threshold=80):
    global attack
    # sp 21
    r.add_vehicle(filter='jeep*')
    if attack:
        attack = activate_attack(r, 'cola', 100, True)
    while True:
        time.sleep(.1)
        # dist = distance_from_driver(driver_g, r)
        # print(dist)
        if int(driver_g.get_location().y) < threshold:
            print('--------------CarlaCola risk activated')
            r.start_vehicle()
            return True


def risk_bike_crossing(r, threshold=55):
    global attack
    # sp 2
    r.add_vehicle(filter='bh*')
    # print("-----------------------value of attack is" + attack)
    if attack:
        attack = activate_attack(r, "bike", 150)
    while True:
        time.sleep(.1)
        dist = _distance_from_driver(driver_g, r)
        # print(dist)
        if int(dist) <= threshold:
            r.start_vehicle()
            return True


def activate_attack(risk_location, attack_string, threshold, special=False):
    while True:
        time.sleep(.1)
        dist = _distance_from_driver(driver_g, risk_location)
        if special:
            dist = driver_g.get_location().y
        if int(dist) <= threshold:
            print("Performing attack")
            return attack_string



# def main():


if __name__ == '__main__':
    init()
