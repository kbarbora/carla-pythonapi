import time

import carla
from carla_exception import *
import math
import sys
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

# ==============================================================================
# -- DualControl -----------------------------------------------------------
# ==============================================================================


class DualControl(object):
    def __init__(self, world, start_in_autopilot, attack, task_level):
        self._autopilot_enabled = start_in_autopilot
        if isinstance(world.player, carla.Vehicle):
            self._control = carla.VehicleControl()
            world.player.set_autopilot(self._autopilot_enabled)
            self._level = task_level
            self._final_loc = carla.Location(x=187, y=55)
        elif isinstance(world.player, carla.Walker):
            self._control = carla.WalkerControl()
            self._autopilot_enabled = False
            self._rotation = world.player.get_transform().rotation
        else:
            raise NotImplementedError("Actor type not supported")
        self._steer_cache = 0.0
        if attack:
            self._steer_attack = attack['values'][1]
            self._throttle_attack = attack['values'][2]
            self._brake_attack = attack['values'][3]
            self._attack_repetitions = int(attack['repetitions'])
            self._attack_restablished = int(attack['restablished'])
            self._attack_interval = int(attack['interval'])
            self._attack_ended = False
        self._attack_control = False
        self.k_values = [1.0, 1.0, 1.0]
        world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)

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
            elif event.type == pygame.JOYBUTTONDOWN:
                print("Button pressed in Joystick ->" + str(event.button))
                if event.button == 7:
                    raise RestartTask
                if event.button == 6:
                    current_loc = world.player.get_transform().location
                    print(current_loc)
                    if current_loc.x < 190 and (self._final_loc.y-15) < current_loc.y < self._final_loc.y:
                        if self._level == 0:
                            print("Next task")
                            raise NextTask
                        else:
                            print("Last task")
                            raise LastTask
                elif event.button == 1:
                    world.hud.toggle_info()
                elif event.button == 2:
                    world.camera_manager.toggle_camera()
                elif event.button == 3:
                    world.next_weather()
                elif event.button == self._reverse_idx:
                    self._control.gear = 1 if self._control.reverse else -1
                elif event.button == 23:
                    world.camera_manager.next_sensor()

            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                elif event.key == K_BACKSPACE:
                    world.restart()
                elif event.key == K_F1:
                    world.hud.toggle_info()
                elif event.key == K_h or (event.key == K_SLASH and pygame.key.get_mods() & KMOD_SHIFT):
                    world.hud.help.toggle()
                elif event.key == K_TAB:
                    world.camera_manager.toggle_camera()
                elif event.key == K_c and pygame.key.get_mods() & KMOD_SHIFT:
                    world.next_weather(reverse=True)
                elif event.key == K_c:
                    world.next_weather()
                elif event.key == K_BACKQUOTE:
                    world.camera_manager.next_sensor()
                elif event.key > K_0 and event.key <= K_9:
                    world.camera_manager.set_sensor(event.key - 1 - K_0)
                elif event.key == K_r:
                    world.camera_manager.toggle_recording()
                if isinstance(self._control, carla.VehicleControl):
                    if event.key == K_q:
                        self._control.gear = 1 if self._control.reverse else -1
                    elif event.key == K_m:
                        self._control.manual_gear_shift = not self._control.manual_gear_shift
                        self._control.gear = world.player.get_control().gear
                        world.hud.notification('%s Transmission' %
                                               ('Manual' if self._control.manual_gear_shift else 'Automatic'))
                    elif self._control.manual_gear_shift and event.key == K_COMMA:
                        self._control.gear = max(-1, self._control.gear - 1)
                    elif self._control.manual_gear_shift and event.key == K_PERIOD:
                        self._control.gear = self._control.gear + 1
                    elif event.key == K_p:
                        self._autopilot_enabled = not self._autopilot_enabled
                        world.player.set_autopilot(self._autopilot_enabled)
                        world.hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))

        if not self._autopilot_enabled:
            if isinstance(self._control, carla.VehicleControl):
                # self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
                if self._attack_control and (not self._attack_ended):
                    self._parse_vehicle_wheel_attack()
                self._parse_vehicle_wheel()
                self._control.reverse = self._control.gear < 0
            # elif isinstance(self._control, carla.WalkerControl):
            #     self._parse_walker_keys(pygame.key.get_pressed(), clock.get_time())
            world.player.apply_control(self._control)

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
        throttleCmd = self.k_values[1] * abs((jsInputs[self._throttle_idx] / 2 + .5) - 1)
        if throttleCmd <= 0.01:
            throttleCmd = 0
        elif throttleCmd > 1:
            throttleCmd = 1
        # print(throttleCmd)

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
        numAxes, jsInputs, jsButtons = self._get_joystick()

        modified_values = False
        print("executing Cyberattack!!!")
        if self._steer_attack != '0':  # attacking steering
            delta = self.k_values[0] * int(self._steer_attack[1]) / 100  # calculate change for gas pedal
            exec("self.k_values[0] = self.k_values[0] " + self._steer_attack[0] + " delta")
            modified_values = True
        if self._throttle_attack != '0':  # attacking throttle
            delta = self.k_values[1] * int(self._throttle_attack[1]) / 100  # calculate change for throttle pedal
            exec("self.k_values[1] = self.k_values[1] " + self._throttle_attack[0] + " delta")
            modified_values = True
        if self._brake_attack != '0':  # attacking steering, throttle
            print(str(self.k_values[2]) + ' brake' + self._brake_attack)
            delta = self.k_values[2] * int(self._brake_attack[1]) / 100  # calculate change for brake pedal
            exec("self.k_values[2] = self.self.k_values[2] " + self._brake_attack[0] + " delta")
            modified_values = True
        if not modified_values:
            raise (Exception("[Error] Attack value not identified "))
        self._attack_repetitions -= 1
        self._attack_control = False
        return

    def attack_counter(self):
        time.sleep(5)
        print("Starting counter")  # debug
        while True:
            print(self._attack_repetitions)
            if self._attack_repetitions < 0:
                if not self._attack_restablished:
                    print("Skipping restablished")
                else:
                    time.sleep(self._attack_restablished)
                    print("Restablishing k values")
                    self.k_values = [1.0, 1.0, 1.0]
                self._attack_ended = True
                print("Attack finished")
                return
            else:
                time.sleep(self._attack_interval)
                self._attack_control = True

    @staticmethod
    def _is_quit_shortcut(KEY):
        return (KEY == K_ESCAPE) or (KEY == K_q and pygame.key.get_mods() & KMOD_CTRL)
