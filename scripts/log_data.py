#!/usr/bin/python
import argparse
import glob, os, sys, random, time, traceback
sys.path.append('../carla/dist/carla-0.9.5-py3-linux-x86_64.egg')
# try:
#     sys.path.append(glob.glob('../carla/dist/carla-*%d-%s.egg' % (
#         sys.version_info.major,
#         'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
# except IndexError:
#     pass

import carla
from examples.manual_control_steeringwheel import HUD as driving_session

def init():
    try:
        client = carla.Client('localhost', 2000)
        client.set_timeout(2.0)

        #Retrieve world currently running
        world = client.get_world()
    except Exception as err:
        traceback.print_tb(err.__traceback__)
    finally:
        return world


def get_driving_data():
    return driving_session.get_driving_data()


def get_dict():
    """
    Get the driving data for the current running server
    :return:
    """
    world = init()
    data = dict()

    # The world contains the blueprints list that we can use for adding new
    # actors into the simulation
    library_bp = world.get_blueprint_library()

    # Filter all the blueprints of type 'vehicle'
    vehicle_bp = library_bp.filter('vehicle')
    driver = world.player

    # Get the joystick parameters
    joystick = driver.get_control()

    # Get the current data
    location = driver.get_transform()
    velocity = driver.getvelocity()
    acceleration = driver.getacceleration()
    throttle = joystick.throttle
    steer = joystick.steer
    brake = joystick.brake
    reverse = joystick.reverse
    hand_brake = joystick.hand_brake
    manual = joystick.manual_gear_shift

    # Store the data in the dictonary
    data['location'] = location
    data['velocity'] = velocity
    data['acceleration'] = acceleration
    data['throttle'] = throttle
    data['steer'] = steer
    data['brake'] = brake
    data['reverse'] = reverse
    data['hand brake'] = hand_brake
    data['manual'] = manual

    return data

def main():
    argparser = argparse.ArgumentParser(
        description='CARLA Driving Data logger')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='actor filter (default: "vehicle.*")')
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]


while True:
    print(get_driving_data())


