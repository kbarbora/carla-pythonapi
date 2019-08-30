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
import manual_control_steeringwheel as ControlSW
import spawn_npc as SpawnNPC
import carla

def main():

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
        help='window resolution (default: 1280x720)')
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
        help='username-driver identification number (00)')
    argparser.add_argument(
        '-n', '--number-of-vehicles',
        metavar='N',
        default=0,
        type=int,
        help='number of vehicles (default: 10)')
    argparser.add_argument(
        '-w', '--number-of-walkers',
        metavar='W',
        default=0,
        type=int,
        help='number of walkers (default: 50)')
    argparser.add_argument(
        '--safe',
        action='store_true',
        help='avoid spawning vehicles prone to accidents')
    argparser.add_argument(
        '--filterv',
        metavar='PATTERN',
        default='vehicle.*',
        help='vehicles filter (default: "vehicle.*")')
    argparser.add_argument(
        '--filterw',
        metavar='PATTERN',
        default='walker.pedestrian.*',
        help='pedestrians filter (default: "walker.pedestrian.*")')
    args = argparser.parse_args()
    vehicles_list = []
    walkers_list = []
    all_id = []
    try:
        _thread.start_new_thread(SpawnNPC.main, (args, vehicles_list, walkers_list, all_id))
        # SpawnNPC.main(args)
        clock = pygame.time.Clock()
        ControlSW.start(args, clock)
    finally:
        client = carla.Client(args.host, args.port)
        print('destroying %d vehicles' % len(vehicles_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])

        # stop walker controllers (list is [controler, actor, controller, actor ...])
        for i in range(0, len(all_id), 2):
            client.get_world().get_actors(all_id)[i].stop()

        print('destroying %d walkers' % len(walkers_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in all_id])


if __name__ == '__main__':
    main()
