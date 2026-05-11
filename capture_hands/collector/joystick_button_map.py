class JoystickButtonMap():
    def init_stick_directions(self):
        self.stick_direction = {
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
    
class JoystickLeftButtonMap(JoystickButtonMap):
    def init_map(self, is_xbox_type=False):
        super().__init__()
        self.axis = {"stick": (0, 1)}
        self.buttons = {
            "button_A": 0,     # A (Xbox) / X (PlayStation)
            "button_B": 1,     # B (Xbox) / Circle (PlayStation)
            "button_X": 2,     # X (Xbox) / Square (PlayStation)
            "button_Y": 3,     # Y (Xbox) / Triangle (PlayStation)
        }

class JoystickRightButtonMap(JoystickButtonMap):
    def init_map(self, is_xbox_type=False):
        super().__init__()
        self.axis = {"stick": (3, 4) if is_xbox_type else (2, 3)}
        self.dpad_direction = {
            (0, 1): 'up',
            (0, -1): 'down',
            (-1, 0): 'left',
            (1, 0): 'right',
        }

class JoystickTriggersButtonMap(JoystickButtonMap):
    def init_map(self, is_xbox_type=False):
        self.axis = {
            "trigger_L": 2 if is_xbox_type else 4,
            "trigger_R": 5,
        }
        self.buttons = {
            "bumper_L": 4,     # LB (Xbox) / L1 (PlayStation)
            "bumper_R": 5,     # RB (Xbox) / R1 (PlayStation)
            "trigger_L": 6,
            "trigger_R": 7,
        }