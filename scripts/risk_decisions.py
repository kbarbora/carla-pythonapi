import carla
import scripts.pedestrian as pedestrian
import scripts.vehicle as vehicle


class risk_situation:

    def __init__(self):
        nonlocal world
        self.orientation = '0'
        self.location = carla.Location(x=0, y=0, z=0)
        self.vehicle = []
        self.pedestrian = []
        self.run = False
        #_snapshot = world.wait_for_tick()
        self.timestamp = None

    def add_vehicle(self, location):
        nonlocal world
        sp = carla.Transform(location, carla.Rotation(pitch=0, yaw=0.0001, roll=0))
        _vehicle = vehicle.spawn_vehicle(world, sp)




    def add_pedestrian(self, pedestrian):
        nonlocal world





def init():
    client = carla.Client('127.0.0.1', 2000)
    world = client.get_world()
    return world
