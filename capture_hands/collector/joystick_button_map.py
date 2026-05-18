import itertools
from abc import abstractmethod

class JoystickInput():
    def __init__(self, name, data, map):
        self.name = name
        self.symbol = name
        self.data = data
        self.map = map
    
    def __init__(self, map, name, data, symbol=None):
        self.name = name
        self.data = data
        self.map = map
        if symbol:
            self.symbol = symbol
        else:
            self.symbol = name.replace('_', ' ').capitalize()
    
    @abstractmethod
    def resolve(self):
        self.data.get_value_for(self.map)

class JoystickData():
    def __init__(self, value):
        self.value = value

    @abstractmethod
    def get_value_for(self, map):
        pass
    
class StickData(JoystickData):
    def get_value_for(self, map):
        map.resolve_stick(self.value)

class ButtonData(JoystickData):
    def get_value_for(self, map):
        map.resolve_button(self.value)

class DpadData(JoystickData):
    def get_value_for(self, map):
        map.resolve_dpad(self.value)

class TriggerData(JoystickData):
    def get_value_for(self, map):
        map.resolve_trigger(self.value)

class JoystickButtonMap():
    def __init__(self):
        self.buttons = []
        self.stick = None
        self.stick_directions = []
        self.dpad_directions = []
        self.capture = None

    def set_capture(self, capture):
        self.capture = capture

    def init_stick_directions(self):
        self.stick_directions = [
            JoystickInput(self, "stick_up", StickData((0, -1)), "⇑"),
            JoystickInput(self, "stick_down", StickData((0, 1)), "⇓"),
            JoystickInput(self, "stick_left", StickData((-1, 0)), "⇐"),
            JoystickInput(self, "stick_right", StickData((1, 0)), "⇒"),
            JoystickInput(self, "stick_neutral", StickData((0, 0)), "-"),
            JoystickInput(self, "stick_up_left", StickData((-1, -1)), "⇖"),
            JoystickInput(self, "stick_up_right", StickData((1, -1)), "⇗"),
            JoystickInput(self, "stick_down_left", StickData((-1, 1)), "⇙"),
            JoystickInput(self, "stick_down_right", StickData((1, 1)), "⇘"),
        ]

    def get_buttons(self):
        return self.buttons

    def get_sticks(self):
        return self.stick_directions
    
    def get_dpads(self):
        return self.dpad_directions

    def __iter__(self):
        return itertools.chain(self.stick_directions, self.dpad_directions, self.buttons)

    def resolve_input(self, joystick_input):
        joystick_input.resolve()
    
    def resolve_button(self, button_index):
        self.capture.get_button(button_index)
    
    def resolve_stick(self, direction):
        self.capture.get_stick(self.stick_axis, direction)
    
    def resolve_dpad(self, direction):
        self.capture.get_dpad(direction)
    
    def resolve_trigger(self, axis):
        self.capture.get_trigger(axis)

class JoystickLeftButtonMap(JoystickButtonMap):
    def init_map(self, capture, is_xbox_type=False):
        self.set_capture(capture)
        self.init_stick_directions()
        self.stick_axis = (0, 1)
        self.buttons = [
            JoystickInput(self, "A", ButtonData(0)), # A (Xbox) / X (PlayStation)
            JoystickInput(self, "B", ButtonData(1)), # B (Xbox) / Circle (PlayStation)
            JoystickInput(self, "X", ButtonData(2)), # X (Xbox) / Square (PlayStation)
            JoystickInput(self, "Y", ButtonData(3)), # Y (Xbox) / Triangle (PlayStation)
        ]

class JoystickRightButtonMap(JoystickButtonMap):
    def init_map(self, capture, is_xbox_type=False):
        self.set_capture(capture)
        self.init_stick_directions()
        self.stick_axis = (3, 4) if is_xbox_type else (2, 3)
        self.dpad_directions = [
            JoystickInput(self, 'up', DpadData((0, -1))), 
            JoystickInput(self, 'down', DpadData((0, 1))), 
            JoystickInput(self, 'left', DpadData((-1, 0))), 
            JoystickInput(self, 'right', DpadData((1, 0))), 
            JoystickInput(self, 'neutral', DpadData((0, 0))),
        ]

class JoystickTriggersButtonMap(JoystickButtonMap):
    def init_map(self, capture, is_xbox_type=False):
        self.set_capture(capture)
        self.buttons = [
            JoystickInput(self, 'L1', ButtonData(4)),     # LB (Xbox) / L1 (PlayStation)
            JoystickInput(self, 'R1', ButtonData(5)),     # RB (Xbox) / R1 (PlayStation)
            JoystickInput(self, "L2", TriggerData(2 if is_xbox_type else 4)),
            JoystickInput(self, "R2", TriggerData(5))
            # 'L2': 6,
            # 'R2': 7,
        ]