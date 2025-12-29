import os
from renderer import Renderer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class RendererRight(Renderer):
    def __init__(self, screen, app):
        self.name = "RIGHT"
        BUTTON_FILES = {
            # Sticks
            'stick_right_neutral': 'stick_center.png',
            'stick_right_up': 'stick_up.png',
            'stick_right_down': 'stick_down.png',
            'stick_right_left': 'stick_left.png',
            'stick_right_right': 'stick_right.png',
            'stick_right_up_left': 'stick_up_left.png',
            'stick_right_up_right': 'stick_up_right.png',
            'stick_right_down_left': 'stick_down_left.png',
            'stick_right_down_right': 'stick_down_right.png',
            
            # Botones de acción
            'button_A': 'gamepad_a.png',
            'button_B': 'gamepad_b.png',
            'button_X': 'gamepad_x.png',
            'button_Y': 'gamepad_y.png',
        }

        BUTTON_STATES = {
            # Stick derecho 
            'stick_right_up_left': False,
            'stick_right_up': False,
            'stick_right_up_right': False,
            'stick_right_left': False,
            'stick_right_neutral': False,
            'stick_right_right': False,
            'stick_right_down_left': False,
            'stick_right_down': False,
            'stick_right_down_right': False,
            
            # Botones del gamepad derecho 
            'button_A': False,
            'button_B': False,
            'button_X': False,
            'button_Y': False,
        }

        super().__init__(screen, app, "Lado Derecho - Stick + A/B/X/Y", BUTTON_STATES, BUTTON_FILES, True)

    def draw_buttons(self):
        self.draw_sticks_display()
        self.draw_gamepad_buttons(['button_Y', 'button_X', 'button_A', 'button_B']) 

    def get_active_button_label(self, active_button):
        return active_button.replace('_', ' ').title()