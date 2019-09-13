# ==============================================================================
# University of Texas at San Antonio
#
#   Author: Kevin Barba
# ==============================================================================

"""
Functions to draw the buttons using PyGame
"""


from pygame \
    import Color, draw, SRCALPHA, transform, \
    Rect, Surface, BLEND_RGBA_MAX, BLEND_RGBA_MIN
import pygame.mouse

FONT_PATH = '../config/meta-normal.ttf'


def text_objects(text, font, color):
    textSurface = font.render(text, True, color)
    return textSurface, textSurface.get_rect()


def button_action(display, position, dimensions, color, text, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    bright_color = [(color[0]+30) % 256, (color[1]+30) % 256, (color[2]+30) % 256]
    # for i in range(3):
    #     bright_color[i] = bright_color[i] if bright_color[i] < 255 else 255
    button = (position[0], position[1], dimensions[0], dimensions[1])
    if button[0]+button[2] > mouse[0] > button[0] and\
            button[1]+button[3] > mouse[1] > button[1]:
        filledRoundedRect(display,  button, bright_color)
        if click[0] == 1 and action != None:
            print('yey')
    else:
        filledRoundedRect(display,  button, color)
    font = pygame.font.Font(FONT_PATH, 20)
    text_surf, text_rect = text_objects(text, font, (255, 255, 255))
    text_rect.center = (button[0]+(button[2]/2), (button[1]+button[3]/2))
    display.blit(text_surf, text_rect)


def filledRoundedRect(surface, rect, color, radius=0.4):
    """
    filledRoundedRect(surface, rect, color, radius=0.4)

    surface : destination
    rect    : rectangle
    color   : rgb or rgba
    radius  : 0 <= radius <= 1
    """
    rect = Rect(rect)
    color = Color(*color)
    alpha = color.a
    color.a = 0
    pos = rect.topleft
    rect.topleft = 0, 0
    rectangle = Surface(rect.size, SRCALPHA)

    circle = Surface([min(rect.size)*3]*2, SRCALPHA)
    draw.ellipse(circle, (0, 0, 0), circle.get_rect(), 0)
    circle = transform.smoothscale(circle, [int(min(rect.size)*radius)]*2)

    radius = rectangle.blit(circle, (0, 0))
    radius.bottomright = rect.bottomright
    rectangle.blit(circle, radius)
    radius.topright = rect.topright
    rectangle.blit(circle, radius)
    radius.bottomleft = rect.bottomleft
    rectangle.blit(circle, radius)

    rectangle.fill((0, 0, 0), rect.inflate(-radius.w, 0))
    rectangle.fill((0, 0, 0), rect.inflate(0, -radius.h))

    rectangle.fill(color, special_flags=BLEND_RGBA_MAX)
    rectangle.fill((255, 255, 255, alpha), special_flags=BLEND_RGBA_MIN)

    return surface.blit(rectangle, pos)
