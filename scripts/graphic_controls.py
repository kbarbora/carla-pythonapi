from text import FadingText, HelpText
import sys
import glob
import os
import pygame
import datetime
import time
import math
import weakref
import steering_wheel_control as ControlSW
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla
from carla import ColorConverter as cc
try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

# ==============================================================================
# -- CameraManager -------------------------------------------------------------
# ==============================================================================

"""
Welcome to CARLA driving simulator.
Instructions:
    Use steering wheel to change the direction
    Use gas pedal (right pedal) to accelerate
    Use brake pedal (left pedal) to stop
    Use left paddle in steering wheel to enable/disable reverse
    Use R2 button in steering wheel to advance to the next task (need to be at the end position)
    Use L2 button to restart the current task
    Use option button to display this screen


"""

DATA_INTERVAL = 0.5

class CameraManager(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None
        self.surface = None
        self._parent = parent_actor
        self.hud = hud
        self.recording = False
        self._camera_transforms = [
            # carla.Transform(carla.Location(x=-0.1, y=-.3, z=1.2), carla.Rotation(yaw=5)),
            carla.Transform(carla.Location(x=-0.25, y=-.3, z=1.2), carla.Rotation(yaw=5)),
            # carla.Transform(carla.Location(x=-0.5, y=-.4, z=1.2)),
            carla.Transform(carla.Location(x=-5.5, z=2.8), carla.Rotation(pitch=-15))]
        self.transform_index = 1
        self.sensors = [
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB']]
            # ['sensor.camera.depth', cc.Raw, 'Camera Depth (Raw)'],
            # ['sensor.camera.depth', cc.Depth, 'Camera Depth (Gray Scale)'],
            # ['sensor.camera.depth', cc.LogarithmicDepth, 'Camera Depth (Logarithmic Gray Scale)'],
            # ['sensor.camera.semantic_segmentation', cc.Raw, 'Camera Semantic Segmentation (Raw)'],
            # ['sensor.camera.semantic_segmentation', cc.CityScapesPalette,
            #     'Camera Semantic Segmentation (CityScapes Palette)'],
            # ['sensor.lidar.ray_cast', None, 'Lidar (Ray-Cast)']]
        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()
        for item in self.sensors:
            bp = bp_library.find(item[0])
            if item[0].startswith('sensor.camera'):
                bp.set_attribute('image_size_x', str(hud.dim[0]))
                bp.set_attribute('image_size_y', str(hud.dim[1]))
            # elif item[0].startswith('sensor.lidar'):
            #     bp.set_attribute('range', '5000')
            item.append(bp)
        self.index = None

    def toggle_camera(self):
        self.transform_index = (self.transform_index + 1) % len(self._camera_transforms)
        self.sensor.set_transform(self._camera_transforms[self.transform_index])

    def set_sensor(self, index, notify=True):
        index = index % len(self.sensors)
        needs_respawn = True if self.index is None \
            else self.sensors[index][0] != self.sensors[self.index][0]
        if needs_respawn:
            if self.sensor is not None:
                self.sensor.destroy()
                self.surface = None
            self.sensor = self._parent.get_world().spawn_actor(
                self.sensors[index][-1],
                self._camera_transforms[self.transform_index],
                attach_to=self._parent)
            # We need to pass the lambda a weak reference to self to avoid
            # circular reference.
            weak_self = weakref.ref(self)
            self.sensor.listen(lambda image: CameraManager._parse_image(weak_self, image))
        if notify:
            self.hud.notification(self.sensors[index][2])
        self.index = index

    def next_sensor(self):
        self.set_sensor(self.index + 1)

    def toggle_recording(self):
        self.recording = not self.recording
        self.hud.notification('Recording %s' % ('On' if self.recording else 'Off'))

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if not self:
            return
        if self.sensors[self.index][0].startswith('sensor.lidar'):
            points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
            points = np.reshape(points, (int(points.shape[0] / 3), 3))
            lidar_data = np.array(points[:, :2])
            lidar_data *= min(self.hud.dim) / 100.0
            lidar_data += (0.5 * self.hud.dim[0], 0.5 * self.hud.dim[1])
            lidar_data = np.fabs(lidar_data) # pylint: disable=E1111
            lidar_data = lidar_data.astype(np.int32)
            lidar_data = np.reshape(lidar_data, (-1, 2))
            lidar_img_size = (self.hud.dim[0], self.hud.dim[1], 3)
            lidar_img = np.zeros(lidar_img_size)
            lidar_img[tuple(lidar_data.T)] = (255, 255, 255)
            self.surface = pygame.surfarray.make_surface(lidar_img)
        else:
            image.convert(self.sensors[self.index][1])
            array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
            array = np.reshape(array, (image.height, image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if self.recording:
            image.save_to_disk('_out/%08d' % image.frame)


class HUD(object):
    def __init__(self, args, log, doc):
        self.dim = (args.width, args.height)
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        fonts = [x for x in pygame.font.get_fonts() if 'mono' in x]
        default_font = 'ubuntumono'
        mono = pygame.font.match_font(default_font)
        self.args = args
        self._font_mono = pygame.font.Font(mono, 26)
        self._notifications = FadingText(font, (self.dim[0], 40), (0, self.dim[1] - 40))
        self.help = HelpText(pygame.font.Font(mono, 20), self.dim[0]+300, self.dim[1], doc)
        self.server_fps = 0
        self.frame = 0
        self.simulation_time = 0
        self._show_info = True
        self._info_text = []
        self.log_data = ""
        self.log = log
        self._server_clock = pygame.time.Clock()
        if args.cyberattack:
            self.attack = True
        else:
            self.attack = False

    def on_world_tick(self, timestamp):
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        self.frame = timestamp.frame
        self.simulation_time = timestamp.elapsed_seconds

    def tick(self, world, clock):
        global speed
        self._notifications.tick(world, clock)
        if not self._show_info:
            return
        t = world.player.get_transform()
        v = world.player.get_velocity()
        c = world.player.get_control()

        sl = world.player.get_speed_limit()
        # print(sl)
        speed_kmh = 3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)
        speed = speed_kmh / 1.609       # show km/h to mph conversion
        delta_sl = 0
        if speed > sl:
            delta_sl = speed - sl

        # @TODO: traffic light feature not working properly
        traffic_light = world.player.get_traffic_light_state()
        if str(traffic_light) == 'Red':
            encounter_red_light = True
            stopped_at_red_light = True if speed <= 1 else False
            # print("RED LIGHT")
            # print('Stoped: ' + str(stopped_at_red_light))
        else:
            encounter_red_light = False
            stopped_at_red_light = False

        physics = world.player.get_physics_control()
        # torque_curve = physics.torque_curve
        max_rpm = str(physics.max_rpm)[0:4]
        # moi = str(physics.moi)[0:4]
        # drft = str(physics.damping_rate_full_throttle)[0:4]
        # drztce = str(str(physics.damping_rate_zero_throttle_clutch_engaged))[0:4]
        # drztcd = str(physics.damping_rate_zero_throttle_clutch_disengaged)[0:4]
        # automatic_trans = str(physics.use_gear_autobox)
        # gear_switch_time = str(physics.gear_switch_time)[0:4]
        # clutch_strength = str(physics.clutch_strength)[0:4]
        # final_ratio = str(physics.final_ratio)[0:4]
        # forward_gears = physics.forward_gears
        # mass = str(physics.mass)
        # drag_coefficient = str(physics.drag_coefficient)[0:4]
        # center_of_mass = str(physics.center_of_mass.x)[0:4] + ' ' + str(physics.center_of_mass.y)[0:4] + ' ' + str(physics.center_of_mass.z)[0:4]
        # steering_curve = str(physics.steering_curve)
        # wheels = str(physics.wheels)

        heading = 'N' if abs(t.rotation.yaw) < 89.5 else ''
        heading += 'S' if abs(t.rotation.yaw) > 90.5 else ''
        heading += 'E' if 179.5 > t.rotation.yaw > 0.5 else ''
        heading += 'W' if -0.5 > t.rotation.yaw > -179.5 else ''
        vehicles = world.world.get_actors().filter('vehicle.*')

        # elapsed_time = str(datetime.timedelta(seconds=int(self.simulation_time)))[2:]
        controller = ControlSW.controller
        vehicle_counter = 0
        if len(vehicles) > 1:
            distance = lambda l: math.sqrt((l.x - t.location.x)**2 + (l.y - t.location.y)**2 + (l.z - t.location.z)**2)
            vehicles = [(distance(x.get_location()), x) for x in vehicles if x.id != world.player.id]
            for d, vehicle in sorted(vehicles):
                if d > 100.0:
                    break
                vehicle_counter += 1
        # @todo Remove Audi at the beginnning
        text = '' if 'Au' in self._notifications.text else self._notifications.text
        self._info_text = [
            'Speed:   % 1.0f /% 1.0f ' % (speed, sl),
            ('Steer:', c.steer, -1.0, 1.0)]
        self.log_data = \
            '{:.3f},'.format(self.simulation_time) + \
            '{:.2f},'.format(speed) + \
            '{:.2f}{},'.format(t.rotation.yaw, heading) + \
            '{:.2f} {:.2f},'.format(t.location.x, t.location.y) + \
            '{:.2f},'.format(c.throttle) + \
            '{:.2f},'.format(c.steer) + \
            '{:.2f},'.format(c.brake) + \
            '{},'.format(c.reverse) + \
            '{},'.format(vehicle_counter) + \
            '{:.2f},'.format(delta_sl) + \
            '{},'.format(encounter_red_light) + \
            '{},'.format(stopped_at_red_light) + \
            '{},'.format(max_rpm) + \
            text + ','
            # ',' + moi + \
            # ',' + drft + \
            # ',' + drztcd + \
            # ',' + drztcd + \
            # ',' + final_ratio + \
            # ',' + mass + \
            # ',' + drag_coefficient + \
            # ',' + center_of_mass + \
        if self.attack:
            self.log_data += '{},'.format(controller.attack_activate) + \
                             '{}/{}/{},'.format(''.join(controller.steer_attack), ''.join(controller.throttle_attack), ''.join(controller.brake_attack)) + \
                             '{},'.format(controller.delta) + \
                             '{},'.format(controller.attack_repetitions) + \
                             '{}/{}/{},'.format(controller.k_values[0], controller.k_values[1], controller.k_values[2]) + \
                             '{}'.format(controller.attack_ended)
        return

    def write_driving_data(self, keep_writing=False):
        counter = 0
        while True:
            if counter > 0:
                try:
                    self.log.write('{},{}\n'.format(counter, self.log_data))
                except Exception:
                    self.log.write('{},{}\n'.format(counter, self.log_data))
                    self.log.close()
            # log.write(str(counter) +',' +self.log_data + '\n')
            time.sleep(DATA_INTERVAL)  # log data interval
            counter += 1
            if not keep_writing:
                break
        return

    def toggle_info(self):
        self._show_info = not self._show_info

    def notification(self, text, seconds=2.0):
        self._notifications.set_text(text, seconds=seconds)

    def error(self, text):
        self._notifications.set_text('Error: %s' % text, (255, 0, 0))

    def render(self, display):
        # if not self._show_info:
        if self._show_info:
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            for item in self._info_text:
                if isinstance(item, tuple):
                    rect_border = pygame.Rect((1200 + bar_h_offset, v_offset + 815), (bar_width, 8))
                    pygame.draw.rect(display, (255, 255, 255), rect_border, 1)
                    f = (item[1] - item[2]) / (item[3] - item[2])
                    if item[2] < 0.0:
                        rect = pygame.Rect((1200 + bar_h_offset + f * (bar_width - 6), v_offset + 815), (6, 6))
                    else:
                        rect = pygame.Rect((1200 + bar_h_offset, v_offset + 815), (f * bar_width, 6))
                    pygame.draw.rect(display, (255, 255, 255), rect)
                    item = item[0]
                if item:  # At this point has to be a str.
                    surface = self._font_mono.render(item, True, (255, 255, 255))
                    display.blit(surface, (1200, v_offset + 800))
                v_offset += 18
        self._notifications.render(display)
        self.help.render(display)
