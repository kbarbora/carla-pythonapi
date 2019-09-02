import time
import pygame
from pygame.draw import rect as Rect
import carla
import sys
try:
    sys.path.append('../util')
except IndexError:
    pass
import carla_parser
from buttons import *


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (100, 255, 0)
ORANGE = [241, 90, 34]
BRIGHT_ORANGE = (230, 127, 90)
UTSA = (12, 35, 64)
FONT_PATH = '../config/meta-normal.ttf'
# BUTTON_FONT = pygame.font.Font(FONT_PATH, 16)


def text_objects(text, font):
    textSurface = font.render(text, True, WHITE)
    return textSurface, textSurface.get_rect()


def intro(args):
    intro_control = True
    while intro_control:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)
        display.fill(UTSA)
        font = pygame.font.Font(FONT_PATH, 26)  # ubuntu dependent
        text_surf, text_rect = text_objects("Welcome to driving simulation", font)
        text_rect.center = ((args.width/2), (args.height/2))
        display.blit(text_surf, text_rect)

        button_action(display, (350, 950), (100, 50), ORANGE, 'Before')
        button_action(display, (550, 950), (100, 50), ORANGE, 'Next')

        pygame.display.update()
        # time.sleep(5)
        # intro_control = False
        # clock.tick(5)


if __name__ == '__main__':
    args = carla_parser.main()
    args.width, args.height = [int(x) for x in args.res.split('x')]
    pygame.init()
    pygame.font.init()
    # clock = pygame.time.Clock()
    intro(args)
