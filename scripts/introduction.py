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


def intro_screen(width, height):
    intro_control = True
    while intro_control:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        display = pygame.display.set_mode(
            (width, height),
            pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        display.fill(UTSA)
        font = pygame.font.Font(FONT_PATH, 26)  # ubuntu dependent
        text_surf, text_rect = text_objects("Welcome to driving simulation", font)
        text_rect.center = ((width/2), (height/2))
        display.blit(text_surf, text_rect)
        bef_button = (width*.25, height*.85)
        next_button = (width * .75, height * .85)
        button_action(display, bef_button, (100, 50), ORANGE, 'Before')
        button_action(display, next_button, (100, 50), ORANGE, 'Next')

        pygame.display.update()
        # time.sleep(5)
        # intro_control = False
        # clock.tick(5)

def driver(args):
    width = args.width
    height = args.height
    intro_screen(width, height)



if __name__ == '__main__':
    args = carla_parser.main()
    args.width, args.height = [int(x) for x in args.res.split('x')]
    pygame.init()
    pygame.font.init()
    # clock = pygame.time.Clock()
    driver(args)
