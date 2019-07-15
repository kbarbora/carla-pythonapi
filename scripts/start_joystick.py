import argparse
import logging
import os
import stat
import datetime
import sys
try:
    sys.path.append('../examples')
except IndexError:
    pass
import manual_control_steeringwheel as ControlSW

def main():
    global args

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
        default='1280x720',
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
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    try:

        ControlSW.game_loop(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


# def create_logfile():
#     if not os.path.isdir(args.log_filepath):
#         # @todo Create custom exception
#         raise Exception("log filepath " + args.log_filepath + " does not exists.")
#
#     dir_permission = os.stat(args.log_filepath)
#     if not bool(dir_permission.st_mode & stat.S_IWUSR):
#         # @todo Create custom exception
#         raise Exception("log filepath: " + args.log_filepath + " has not write permission. Try with sudo.")
#
#     logname = format_logname()
#     return open(args.log_filepath + logname, 'w')
#
#
# def format_logname():
#     time_now = str(datetime.datetime.now()).replace(' ', '-')
#     time_now = time_now[:time_now.index('.')]       # delete anything beyond seconds
#     time_now = time_now.replace(':', '')
#     return str(args.username) + '_' + str(time_now) + ".log"


if __name__ == '__main__':
    main()
