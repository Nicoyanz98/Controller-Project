import itertools
from collector import JoystickInput, JoystickCombination, StickData, DpadData, ButtonData, TriggerData

class JoystickButtonMap():
    def __init__(self, manager):
        self.controller_type = None
        self.buttons = []
        self.stick = None
        self.stick_directions = []
        self.dpad_directions = []
        self.manager = manager
        self.combos = []

        self._init_map()

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

    def get_combos(self):
        return self.combos

    def __iter__(self):
        return itertools.chain(self.stick_directions, self.dpad_directions, self.buttons, self.combos)

    def resolve_input(self, joystick_input, controller_type):
        self.controller_type = controller_type
        pressed = joystick_input.resolve_for(self, controller_type)
        self.controller_type = None
        return pressed
    
    def resolve_button(self, button_index):
        return self.manager.get_button(button_index)
    
    def resolve_stick(self, direction):
        stick_axis = self.stick_axis[self.controller_type] if isinstance(self.stick_axis, list) else self.stick_axis
        return self.manager.get_stick(stick_axis, direction)
    
    def resolve_dpad(self, direction):
        return self.manager.get_dpad(direction)
    
    def resolve_trigger(self, axis):
        return self.manager.get_trigger(axis)

class JoystickLeftButtonMap(JoystickButtonMap):
    def _init_map(self):
        self._init_stick_directions()
        self.stick_axis = (0, 1)
        self.buttons = [
            JoystickInput("A", ButtonData(0)), # A (Xbox) / X (PlayStation)
            JoystickInput("B", ButtonData(1)), # B (Xbox) / Circle (PlayStation)
            JoystickInput("X", ButtonData(2)), # X (Xbox) / Square (PlayStation)
            JoystickInput("Y", ButtonData(3)), # Y (Xbox) / Triangle (PlayStation)
        ]

class JoystickRightButtonMap(JoystickButtonMap):
    def _init_map(self):
        self._init_stick_directions()
        self.stick_axis = [(2, 3), (3, 4)]
        self.dpad_directions = [
            JoystickInput('up', DpadData((0, -1))), 
            JoystickInput('down', DpadData((0, 1))), 
            JoystickInput('left', DpadData((-1, 0))), 
            JoystickInput('right', DpadData((1, 0))), 
            JoystickInput('neutral', DpadData((0, 0))),
        ]

class JoystickTriggersButtonMap(JoystickButtonMap):
    def _init_map(self):
        self.buttons = [
            JoystickInput('L1', ButtonData(4)),     # LB (Xbox) / L1 (PlayStation)
            JoystickInput('R1', ButtonData(5)),     # RB (Xbox) / R1 (PlayStation)
            JoystickInput("L2", TriggerData([4, 2])),
            JoystickInput("R2", TriggerData(5))
            # 'L2': 6,
            # 'R2': 7,
        ]
        for pair in itertools.combinations(self.buttons, 2):
            combo = list(pair)
            combo_name = f"{combo[0].name}+{combo[1].name}"
            self.combos.append(JoystickCombination(combo_name, combo))