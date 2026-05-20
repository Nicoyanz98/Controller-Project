import itertools
from abc import abstractmethod

class JoystickInput():    
    def __init__(self, name, data, symbol=None):
        self.name = name
        self.data = data
        if symbol:
            self.symbol = symbol
        else:
            self.symbol = name.replace('_', ' ').capitalize()
    
    @abstractmethod
    def resolve_for(self, map):
        self.data.get_value_for(map)

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
    def __init__(self, manager, is_xbox_type=False):
        self.buttons = []
        self.stick = None
        self.dpad_directions = []
        self.manager = manager

        self._init_map(is_xbox_type)

    def _init_stick_directions(self):
        self.stick_directions = [
            JoystickInput("stick_up", StickData((0, -1)), "⇑"),
            JoystickInput("stick_down", StickData((0, 1)), "⇓"),
            JoystickInput("stick_left", StickData((-1, 0)), "⇐"),
            JoystickInput("stick_right", StickData((1, 0)), "⇒"),
            JoystickInput("stick_neutral", StickData((0, 0)), "-"),
            JoystickInput("stick_up_left", StickData((-1, -1)), "⇖"),
            JoystickInput("stick_up_right", StickData((1, -1)), "⇗"),
            JoystickInput("stick_down_left", StickData((-1, 1)), "⇙"),
            JoystickInput("stick_down_right", StickData((1, 1)), "⇘"),
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
        joystick_input.resolve_for(self)
    
    def resolve_button(self, button_index):
        self.manager.get_button(button_index)
    
    def resolve_stick(self, direction):
        self.manager.get_stick(self.stick_axis, direction)
    
    def resolve_dpad(self, direction):
        self.manager.get_dpad(direction)
    
    def resolve_trigger(self, axis):
        self.manager.get_trigger(axis)

class JoystickLeftButtonMap(JoystickButtonMap):
    def _init_map(self, is_xbox_type=False):
        self._init_stick_directions()
        self.stick_axis = (0, 1)
        self.buttons = [
            JoystickInput("A", ButtonData(0)), # A (Xbox) / X (PlayStation)
            JoystickInput("B", ButtonData(1)), # B (Xbox) / Circle (PlayStation)
            JoystickInput("X", ButtonData(2)), # X (Xbox) / Square (PlayStation)
            JoystickInput("Y", ButtonData(3)), # Y (Xbox) / Triangle (PlayStation)
        ]

class JoystickRightButtonMap(JoystickButtonMap):
    def _init_map(self, capture, is_xbox_type=False):
        self._init_stick_directions()
        self.stick_axis = (3, 4) if is_xbox_type else (2, 3)
        self.dpad_directions = [
            JoystickInput('up', DpadData((0, -1))), 
            JoystickInput('down', DpadData((0, 1))), 
            JoystickInput('left', DpadData((-1, 0))), 
            JoystickInput('right', DpadData((1, 0))), 
            JoystickInput('neutral', DpadData((0, 0))),
        ]

class JoystickTriggersButtonMap(JoystickButtonMap):
    def _init_map(self, capture, is_xbox_type=False):
        self.buttons = [
            JoystickInput('L1', ButtonData(4)),     # LB (Xbox) / L1 (PlayStation)
            JoystickInput('R1', ButtonData(5)),     # RB (Xbox) / R1 (PlayStation)
            JoystickInput("L2", TriggerData(2 if is_xbox_type else 4)),
            JoystickInput("R2", TriggerData(5))
            # 'L2': 6,
            # 'R2': 7,
        ]