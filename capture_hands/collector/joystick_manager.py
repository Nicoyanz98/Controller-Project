import pygame
from collector import JoystickLeftButtonMap, JoystickRightButtonMap, JoystickTriggersButtonMap

class JoystickManager():
    TRIGGER_THRESHOLD = 0.5
    STICK_THRESHOLD = 0.2

    def __init__(self, window):
        self.window = window

        self.expected_input = None
        self.pressed_expected_input = False

        self.button_maps = {
            "LEFT": JoystickLeftButtonMap(self),
            "RIGHT": JoystickRightButtonMap(self),
            "TRIGGERS": JoystickTriggersButtonMap(self),
        }

        pygame.joystick.init()
        self.joystick_connected = self._check_joystick_connection()

    def _check_joystick_connection(self):
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

            name = self.joystick.get_name()
            self.joystick_type = 1 if "xbox" in name.lower() else 0

            self.window.notify(f"Joystick connected: {name}", "success")
            return True
        
        self.window.notify("No joystick connected", "error")
        return False

    def listens_for(self, joystick_input):
        self.expected_input = joystick_input

    def get_map_names(self):
        return list(self.button_maps.keys())
    
    def get_button_sections_for(self, map_name):
        button_map = self.button_maps.get(map_name, None)
        if self.button_maps:
            return [button_map.get_buttons(), button_map.get_sticks(), button_map.get_dpads(), button_map.get_combos()]
        return []

    def is_joystick_connected(self):
        self.joystick_connected = self._check_joystick_connection()
        return self.joystick_connected

    def update_expected_input(self, map_name):
        pygame.event.pump()
        if self.expected_input and (button_map := self.button_maps.get(map_name, None)) is not None:
            self._update_active_input_in(button_map)

    def _update_active_input_in(self, button_map):
        pressed = button_map.resolve_input(self.expected_input, self.joystick_type)
        self.pressed_expected_input = pressed

    def get_button(self, button_index):
        return self.joystick.get_button(button_index)

    def get_stick(self, stick_axis, direction):        
        x_axis, y_axis = stick_axis
        x, y = self.joystick.get_axis(x_axis), self.joystick.get_axis(y_axis)
        
        get_direction = lambda value: 0 if abs(value) < self.STICK_THRESHOLD else (1 if value > 0 else -1)
        x_dir, y_dir = get_direction(x), get_direction(y)

        return (x_dir, y_dir) == direction

    def get_dpad(self, direction):
        return self.joystick.get_hat(0) == direction

    def get_trigger(self, trigger_axis):
        return self.joystick.get_axis(trigger_axis) > self.TRIGGER_THRESHOLD
    
    def is_expected_input_pressed(self):
        return self.pressed_expected_input