import pygame
from PySide6.QtCore import QThread, Signal

class JoystickButtonMap():
    def __init__(self, is_xbox_type=False):
        # (x,y) coordinates
        self.axis = {
            "stick_left": (0, 1),
            "stick_right": (3, 4) if is_xbox_type else (2, 3),
            "trigger_L": 2 if is_xbox_type else 4,
            "trigger_R": 5,
        }

        self.button_number = {
            "button_A": 0,     # A (Xbox) / X (PlayStation)
            "button_B": 1,     # B (Xbox) / Circle (PlayStation)
            "button_X": 2,     # X (Xbox) / Square (PlayStation)
            "button_Y": 3,     # Y (Xbox) / Triangle (PlayStation)
            "bumper_L": 4,     # LB (Xbox) / L1 (PlayStation)
            "bumper_R": 5,     # RB (Xbox) / R1 (PlayStation)
            "trigger_L": 6,
            "trigger_R": 7,
        }

        self.stick_directions = {
            (0, 0): "neutral",
            (1, 0): "right",
            (-1, 0): "left", 
            (0, -1): "up",     
            (0, 1): "down",    
            (1, -1): "up_right",
            (-1, -1): "up_left",
            (1, 1): "down_right",
            (-1, 1): "down_left"
        }

        self.dpad_direction = {
            (0, 1): 'up',
            (0, -1): 'down',
            (-1, 0): 'left',
            (1, 0): 'right',
        }

class JoystickThread(QThread):
    error_signal = Signal(str)
    success_signal = Signal(str)

    def __init__(self, parent, name):
        super().__init__(parent)
        self._run_flag = True
        self.name = name
        pygame.init()

    def run(self):
        self._init_joystick()
        # Hear inputs after being allowed to hear them (timed with the image capture)
        # Save input with current video thread image (use parent as middle-man)

    def stop(self):
        self._run_flag = False
        self.wait()
    
    def _init_joystick(self):
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            name = self.joystick.get_name()
            self.buttons_map = JoystickButtonMap(is_xbox_type=("xbox" in name.lower()))

            self.success_signal.emit(f"Joystick conectado: {name}")
        else:
            self.error_signal.emit("No joystick connected")