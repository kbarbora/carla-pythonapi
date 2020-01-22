# ==============================================================================
# University of Texas at San Antonio
#
#   Author: Kevin Barba and UAB
# ==============================================================================

"""Starts the driving simulation using the Logitech G29 steering wheel and pedals

Start the driving simualtion using the steering wheel and the pedals as controls
once the server is running and the script is run with the proper command line
arguments. It uses an thread to spawn any pedestrians and/or vehicles if any.
At the end, it destroys the pedestrians and vehicles created before exiting.
It uses the 'manual_control_steeringwheel' script modified.

"""


import argparse
import logging
import os
import stat
import datetime
import _thread
import sys
import time
import pygame
try:
    sys.path.append('../examples')
except IndexError:
    pass
import steering_wheel_control as ControlSW
import manual_control_attackwheel as ControlWheelAttack
import spawn_npc as SpawnNPC
import task_guide
import carla
import gps_map

vehicles_list = []
walkers_list = []
all_id = []

# @TODO: replace parser for general purpose parser
def main(parse=True, pre_parsed=False):

    if parse:
        args = parser()
    else:
        if not pre_parsed:
            raise Exception("Pre-parsed not completed")
        args = pre_parsed

    # vehicles_list = []
    # walkers_list = []
    # all_id = []
    try:
        _thread.start_new_thread(SpawnNPC.main, (args, vehicles_list, walkers_list, all_id))
        _thread.start_new_thread(task_guide.main, ())
        clock = pygame.time.Clock()
        exit_all = False
        map_pid = os.fork()
        if map_pid == 0:
            null = open(os.devnull, 'w')    # open /dev/null
            sys.stdout = null               # ignore stdout
            gps_map.game_loop(args)
        if args.cyberattack:
            print("Attack mode!")
            values = processes_attack_input(args.cyberattack)
            ControlSW.start(args, clock, values)
        else:
            ControlSW.start(args, clock, None)
    finally:
        destroy_NPC(args)
        # client = carla.Client(args.host, args.port)
        # print('destroying %d vehicles' % len(vehicles_list))
        # client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])
        #
        # # stop walker controllers (list is [controler, actor, controller, actor ...])
        # for i in range(0, len(all_id), 2):
        #     client.get_world().get_actors(all_id)[i].stop()
        #
        # print('destroying %d walkers' % len(walkers_list))
        # client.apply_batch([carla.command.DestroyActor(x) for x in all_id])


def destroy_NPC(args):
    client = carla.Client(args.host, args.port)
    print('destroying %d vehicles' % len(vehicles_list))
    client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])

    # stop walker controllers (list is [controler, actor, controller, actor ...])
    for i in range(0, len(all_id), 2):
        client.get_world().get_actors(all_id)[i].stop()

    print('destroying %d walkers' % len(walkers_list))
    client.apply_batch([carla.command.DestroyActor(x) for x in all_id])
    return


def parser():
    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
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
        default='1920x1080',
        help='window resolution (default: 1920x1080)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='actor filter (default: "vehicle.*")')
    argparser.add_argument(
        '-l', '--log_filepath',
        metavar='L',
        default="../logs/",
        help='recorder duration (auto-stop)')
    argparser.add_argument(
        '-u', '--username',
        metavar='U',
        default=00,
        type=int,
        help="username-driver identification number (00).")
    argparser.add_argument(
        '-n', '--number-of-vehicles',
        metavar='N',
        default=0,
        type=int,
        help="number of vehicles (default: 10).")
    argparser.add_argument(
        '-d', '--data-interval',
        metavar='D',
        default=.05,
        type=float,
        help="the interval of data logging (default: 0.05).")
    argparser.add_argument(
        '-w', '--walkers',
        metavar='W',
        default=0,
        type=int,
        help="number of walkers (default: 50).")
    argparser.add_argument(
        '--safe',
        action='store_true',
        help="avoid spawning vehicles prone to accidents.")
    argparser.add_argument(
        '--filterv',
        metavar='PATTERN',
        default='vehicle.*',
        help="vehicles filter (default: 'vehicle.*')")
    argparser.add_argument(
        '--filterw',
        metavar='PATTERN',
        default='walker.pedestrian.*',
        help="pedestrians filter (default: 'walker.pedestrian.*')")
    argparser.add_argument(
        '-c', '--cyberattack',
        metavar='PATH_TO_ATTACK_FILE',
        # default='cyberattack.txt',
        help="Enable the cyberattacks simulation. Follow by the filepath to the cyber attack values textfile."
             "(default: './cyberattack_values.txt')")
    argparser.add_argument(
        '-t', '--tasklevel',
        metavar='NUMBER_OF_TASK',
        default=0,
        type=int,
        help="Start at the desired task. (default 0).")
    return argparser.parse_args()


def processes_attack_input(file='cyberattack.txt'):
    attack = open(file, 'r').readlines()
    if len(attack) != 7:
        raise Exception("Cyberattack input file malformed.")
    processed = [1]
    for a in attack:
        a = a.strip()
        processed.append(a[a.index('=') + 1:])
        if processed[-1] != '0' and ('+' in processed[-1] or '-' in processed[-1]):
            processed[-1] = [processed[-1][0], processed[-1][1:]]
    print(processed)
    return processed


if __name__ == '__main__':
    main()