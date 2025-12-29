import os
from renderer import Renderer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class RendererLeft(Renderer):
    def __init__(self, screen, app):
        self.name = "LEFT"
        BUTTON_FILES = {
            # Sticks
            'stick_left_neutral': 'stick_center.png',
            'stick_left_up': 'stick_up.png',
            'stick_left_down': 'stick_down.png',
            'stick_left_left': 'stick_left.png',
            'stick_left_right': 'stick_right.png',
            'stick_left_up_left': 'stick_up_left.png',
            'stick_left_up_right': 'stick_up_right.png',
            'stick_left_down_left': 'stick_down_left.png',
            'stick_left_down_right': 'stick_down_right.png',

            # Botones de acción
            'button_UP': 'gamepad_up.png',
            'button_LEFT': 'gamepad_left.png',
            'button_RIGHT': 'gamepad_right.png',
            'button_DOWN': 'gamepad_down.png',
        }

        BUTTON_STATES = {
            # Stick izquierdo 
            'stick_left_up_left': False,
            'stick_left_up': False,
            'stick_left_up_right': False,
            'stick_left_left': False,
            'stick_left_neutral': False,
            'stick_left_right': False,
            'stick_left_down_left': False,
            'stick_left_down': False,
            'stick_left_down_right': False,
            
            # Botones del gamepad izquierdo
            'button_UP': False,
            'button_LEFT': False,
            'button_RIGHT': False,
            'button_DOWN': False,
        }

        super().__init__(screen, app, "Lado Izquierdo - Stick + Flechas", BUTTON_STATES, BUTTON_FILES, True)

    def draw_buttons(self):
        self.draw_sticks_display()
        self.draw_gamepad_buttons(['button_UP', 'button_LEFT', 'button_RIGHT', 'button_DOWN']) 

    def get_active_button_label(self, active_button):
        return active_button.replace('_', ' ').title()