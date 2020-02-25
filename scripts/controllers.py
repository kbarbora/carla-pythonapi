import time

import carla
from carla_exception import *
import _thread
import sys
import steering_wheel_control as ControlSW
import risk_decisions
import video_interface

if sys.version_info >= (3, 0):
    from configparser import ConfigParser
else:
    from ConfigParser import RawConfigParser as ConfigParser

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_0
    from pygame.locals import K_9
    from pygame.locals import K_BACKQUOTE
    from pygame.locals import K_BACKSPACE
    from pygame.locals import K_COMMA
    from pygame.locals import K_DOWN
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_F1
    from pygame.locals import K_LEFT
    from pygame.locals import K_PERIOD
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SLASH
    from pygame.locals import K_SPACE
    from pygame.locals import K_TAB
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_c
    from pygame.locals import K_d
    from pygame.locals import K_h
    from pygame.locals import K_m
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_r
    from pygame.locals import K_s
    from pygame.locals import K_w
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')


    # Format for attacks  : ['steer', 'gas', 'brake','restablished', 'iterations', 'interval']
STEER = 0
GAS = 1
BRAKE = 2
RESTABLISHED = 3
ITER = 4
INTERVAL = 5
SLEEP = .1

# ==============================================================================
# -- DualControl -----------------------------------------------------------
# ==============================================================================


class DualControl(object):

    def __init__(self, world, args):
        self._autopilot_enabled = False
        if isinstance(world.player, carla.Vehicle):
            self._control = carla.VehicleControl()
            world.player.set_autopilot(self._autopilot_enabled)
            self.args = args
            self._level = args.tasklevel
            self._final_loc = carla.Location(x=187, y=55)
        elif isinstance(world.player, carla.Walker):
            self._control = carla.WalkerControl()
            self._rotation = world.player.get_transform().rotation
        else:
            raise NotImplementedError("Actor type not supported")
        self._steer_cache = 0.0
        if self.args.cyberattack:
            self.throttle = self.brake = self.steer = '0'
            self.iterations = self.restablished = self.interval = 0
    # Format for attacks  : ['steer', 'gas', 'brake','restablished', 'iterations', 'interval']
            self.attacks = {'bike'     : ['000', '000', '-50', '10', '0', '00'],
                            'cola'     : ['-20', '000', '000', '15', '1', '05'],
                            'tunnel'   : ['000', '-10', '000', '20', '1', '02'],
                            'sculpture': ['-50', '000', '000', '10', '0', '00'],
                            'inters'   : ['+30', '000', '000', '15', '0', '00'],
                            'combo'    : ['+30', '+50', '+50', '10', '0', '10'],
                            }
            self.attack_activate = False
        self.attack_ended = True
        self.k_values = [1.0, 1.0, 1.0]
        self.delta = 0

        self.video = video_interface.VideoPi()

        self._play_sound = False
        self._acc_sound = SoundEffect.init_sound()['acc']
        self._horn_sound = SoundEffect.init_sound()['horn']
        # self._acc_sound.set_volume(0)
        # self._acc_sound.play()
        # _thread.start_new_thread(SoundEffect.engine_sound_loop, ())
        world.hud.help.toggle()
        # world.hud.notification("Press 'option' or '?' for help.", seconds=4.0)

        # initialize steering wheel
        pygame.joystick.init()

        joystick_count = pygame.joystick.get_count()
        if joystick_count > 1:
            raise ValueError("Please Connect Just One Joystick")

        self._joystick = pygame.joystick.Joystick(0)
        self._joystick.init()

        self._parser = ConfigParser()
        self._parser.read('../config/wheel_config.ini')
        self._steer_idx = int(
            self._parser.get('G29 Racing Wheel', 'steering_wheel'))
        self._throttle_idx = int(
            self._parser.get('G29 Racing Wheel', 'throttle'))
        self._brake_idx = int(self._parser.get('G29 Racing Wheel', 'brake'))
        self._reverse_idx = int(self._parser.get('G29 Racing Wheel', 'reverse'))
        self._handbrake_idx = int(
            self._parser.get('G29 Racing Wheel', 'handbrake'))

    def parse_events(self, world, clock):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.JOYBUTTONDOWN:
                print("Button pressed in Joystick ->" + str(event.button))
                if event.button == 10:
                    self._horn_sound.play()
                if event.button == 7:
                    raise RestartTask
                # if event.button == 6:
                    # current_loc = world.player.get_transform().location
                    # print(current_loc)
                    # if current_loc.x < 190 and (self._final_loc.y-15) < current_loc.y < self._final_loc.y:
                    #     if self._level == 1:
                    #         print("Next task")
                    #         raise NextTask
                    #     else:
                    #         print("Last task")
                    #         raise LastTask
                elif event.button == self._reverse_idx:
                    self._control.gear = 1 if self._control.reverse else -1
                elif event.button == 23:
                    world.camera_manager.next_sensor()
                elif event.button == 9:
                    world.hud.help.toggle()
                    self.video.start_recording(ControlSW.logname + '.h264')

        if isinstance(self._control, carla.VehicleControl):
            if not self.attack_ended:
                self._parse_vehicle_wheel_attack()
            self._parse_vehicle_wheel()
            self._control.reverse = self._control.gear < 0
        world.player.apply_control(self._control)
        return

    def _get_joystick(self):
        numAxes = self._joystick.get_numaxes()
        jsInputs = [float(self._joystick.get_axis(i)) for i in range(numAxes)]
        # print (jsInputs)
        jsButtons = [float(self._joystick.get_button(i)) for i in
                     range(self._joystick.get_numbuttons())]
        return numAxes, jsInputs, jsButtons

    def _parse_vehicle_wheel(self):
        """
        This function will be executed only where there is NOT an attack going on
        """
        numAxes, jsInputs, jsButtons = self._get_joystick()
        # Custom function to map range of inputs [1, -1] to outputs [0, 1] i.e 1 from inputs means nothing is pressed
        # For the steering, it seems fine as it is
        # steerCmd = self.k_values[0] * math.tan(0.78 * jsInputs[self._steer_idx])
        steerCmd = self.k_values[0] * jsInputs[self._steer_idx]

        # @TODO: Disable acceleration at the beginning of the trial
        # throttleCmd = self.k_values[1] + (2.05 * math.log10(
        #     -0.7 * jsInputs[self._throttle_idx] + 1.4) - 1.2) / 0.92
        # print(jsInputs[self._throttle_idx])
        throttleCmd = self.k_values[1] * abs((jsInputs[self._throttle_idx] / 2 + .5) - 1)
        if throttleCmd <= 0.01:
            throttleCmd = 0
        elif throttleCmd > 1:
            throttleCmd = 1

        # @TODO: Disable brake at the beginning of the trial
        brakeCmd = self.k_values[2] * abs(jsInputs[self._brake_idx] - 1)
        # brakeCmd = self.k_values[2] + (2.05 * math.log10(
        #     -0.7 * jsInputs[self._brake_idx] + 1.4) - 1.2) / 0.92
        if brakeCmd <= 0.01:
            brakeCmd = 0
        elif brakeCmd > 1:
            brakeCmd = 1
        # print(brakeCmd)

        self._control.steer = steerCmd
        self._control.brake = brakeCmd
        self._control.throttle = throttleCmd

        #toggle = jsButtons[self._reverse_idx]
        self._control.hand_brake = bool(jsButtons[self._handbrake_idx])
        return

    def _parse_vehicle_wheel_attack(self):
        """
        This function will be executed only where there is an attack going on
        """
        # numAxes, jsInputs, jsButtons = self._get_joystick()
        if self.attack_activate:
            modified_values = False
            print("executing Cyberattack!!!")
            if self.steer != '000':  # attacking steering
                self.delta = self.k_values[0] * int(self.steer[1:]) / 100  # calculate change for gas pedal
                exec("self.delta = self.delta * " + self.steer[0] + "1")       # embed sign in self.delta var
                exec("self.k_values[0] = self.k_values[0] + self.delta")
                modified_values = True
            if self.throttle != '000':  # attacking throttle
                self.delta = self.k_values[1] * int(self.throttle[1:]) / 100  # calculate change for throttle pedal
                exec("self.k_values[1] = self.k_values[1] " + self.throttle[0] + " self.delta")
                modified_values = True
            if self.brake != '000':  # attacking steering, throttle
                self.delta = self.k_values[2] * int(self.brake[1:]) / 100  # calculate change for brake pedal
                exec("self.k_values[2] = self.k_values[2] " + self.brake[0] + " self.delta")
                modified_values = True
            if not modified_values:
                raise (Exception("[Error] Attack value not identified "))
            self.iterations -= 1
            self.attack_activate = False
        return

    def attack_trigger(self):
        while True:
            time.sleep(SLEEP)
            if risk_decisions.attack in self.attacks.keys():
                self.attack_ended = False
                current_attack = self.attacks[risk_decisions.attack]
    # Format for attacks  : ['steer', 'gas', 'brake','restablished', 'iterations', 'interval']
                self.steer = current_attack[STEER]
                self.throttle = current_attack[GAS]
                self.brake = current_attack[BRAKE]
                self.restablished = int(current_attack[RESTABLISHED])
                self.iterations = int(current_attack[ITER])
                self.interval = int(current_attack[INTERVAL])
                if self.attack_counter():
                    self.reset_attack()
                else:
                    raise(Exception("[Error] Attack Reset"))

    def reset_attack(self):
        risk_decisions.attack = "attack"
        self.throttle = self.brake = self.steer = '0'
        self.iterations = self.restablished = self.interval = 0
        return

    # will execute once for each attack
    def attack_counter(self):
        # time.sleep(5)
        print("Starting attack " + risk_decisions.attack)  # debug
        while True:
            # print(self.iterations)
            if self.iterations < 0:
                self.attack_ended = True
                if not self.restablished:
                    print("Skipping restablished")
                else:
                    time.sleep(self.restablished)
                    print("Restablishing k values")
                    self.k_values = [1.0, 1.0, 1.0]
                    return True
                print("Attack finished")
                return False
            else:
                time.sleep(self.interval)
                self.attack_activate = True
                time.sleep(SLEEP)

    @staticmethod
    def _is_quit_shortcut(KEY):
        return (KEY == K_ESCAPE) or (KEY == K_q and pygame.key.get_mods() & KMOD_CTRL)


class SoundEffect(object):

    acc = None
    start = None
    engine = None

    def __init__(self, audio_file, volume=1, channel=0, loop=0):
        self._sound = pygame.mixer.Sound(audio_file)
        self._sound.set_volume(volume)
        self._volume = self._sound.get_volume()
        self._length = self._sound.get_length()
        self._channel = pygame.mixer.Channel(channel)
        self._loop = loop

    def set_channel(self, channel=0):
        self._channel = pygame.mixer.Channel(channel)

    def set_volume(self, volume):
        self._sound.set_volume(volume)
        self._volume = volume

    def play(self, fade=0):
        if fade:
            self._sound.play(loops=-1, fade_ms=fade)
        else:
            self._channel.play(self._sound, loops=self._loop)

    @staticmethod
    def engine_sound_loop():
        door.play()
        time.sleep(3)
        start.play()
        engine.play(fade=3000)
        time.sleep(.5)
        # acc.play()

    @staticmethod
    def init_sound():
        global engine, start, acc, door
        pygame.mixer.init()
        CAR_ENGINE_CH = 1
        START_ENGINE_CH = 2
        MAX_ACC_CH = 3
        HORN = 4
        door = SoundEffect('../media/sound/cardoor.wav')
        horn = SoundEffect('../media/sound/horn.wav', channel=HORN)
        engine = SoundEffect('../media/sound/car_engine.wav', channel=CAR_ENGINE_CH, loop=-1)
        start = SoundEffect('../media/sound/start_engine.wav', channel=START_ENGINE_CH)
        # acc = SoundEffect('../sound/max_acc1.wav', channel=MAX_ACC_CH, volume=1, loop=-1)
        acc = []
        for i in range(2, 12, 2):
            acc.append(SoundEffect('../media/sound/acc'+str(i)+'.wav', channel=MAX_ACC_CH, volume=0))
        return {'door': door, 'start': start, 'engine': engine, 'acc': acc, 'horn': horn}





