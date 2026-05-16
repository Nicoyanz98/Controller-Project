import itertools

class JoystickButtonMap():
    def __init__(self):
        self.buttons = {}
        self.axis = {}
        self.stick_direction = {}
        self.dpad_direction = {}

    def init_stick_directions(self):
        self.stick_direction = {
            "up": ("⇑", (0, -1)),
            "down": ("⇓", (0, 1)), 
            "left": ("⇐", (-1, 0)),
            "right": ("⇒", (1, 0)),
            "neutral": ("-", (0, 0)),
            "up_left": ("⇖", (-1, -1)),
            "up_right": ("⇗", (1, -1)),
            "down_left": ("⇙", (-1, 1)),
            "down_right": ("⇘", (1, 1)),
        }

    def get_sticks(self):
        return [(symbol, f"stick_{direction}", value) for direction, (symbol, value) in self.stick_direction.items()]
    
    def get_buttons(self):
        return [(button, f"button_{button}", value) for button, value in self.buttons.items()]

    def get_dpads(self):
        return [(direction, f"dpad_{direction}", value) for direction, value in self.dpad_direction]

    def __iter__(self):
        return itertools.chain(self.get_buttons(), self.get_sticks(), self.get_dpads())
class JoystickLeftButtonMap(JoystickButtonMap):
    def init_map(self, is_xbox_type=False):
        self.init_stick_directions()
        self.axis = {"stick": (0, 1)}
        self.buttons = {
            'A': 0,     # A (Xbox) / X (PlayStation)
            'B': 1,     # B (Xbox) / Circle (PlayStation)
            'X': 2,     # X (Xbox) / Square (PlayStation)
            'Y': 3,     # Y (Xbox) / Triangle (PlayStation)
        }

class JoystickRightButtonMap(JoystickButtonMap):
    def init_map(self, is_xbox_type=False):
        self.init_stick_directions()
        self.axis = {"stick": (3, 4) if is_xbox_type else (2, 3)}
        self.dpad_direction = {
            'up': (0, -1), 
            'down': (0, 1), 
            'left': (-1, 0), 
            'right': (1, 0), 
            'neutral': (0, 0),
        }

class JoystickTriggersButtonMap(JoystickButtonMap):
    def init_map(self, is_xbox_type=False):
        self.axis = {
            "L2": 2 if is_xbox_type else 4,
            "R2": 5,
        }
        self.buttons = {
            'L1': 4,     # LB (Xbox) / L1 (PlayStation)
            'R1': 5,     # RB (Xbox) / R1 (PlayStation)
            'L2': 6,
            'R2': 7,
        }