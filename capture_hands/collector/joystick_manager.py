from collector import JoystickThread, JoystickLeftButtonMap, JoystickRightButtonMap, JoystickTriggersButtonMap
from PySide6.QtCore import Slot
from functools import partial

class JoystickManager():
    def __init__(self, window, name):
        self.window = window
        self.current_button_map = None
        self.pressed_expected_input = False

        self.thread = JoystickThread(self, "Joystick")
        self.thread.error_signal.connect(partial(self._notify, "error"))
        self.thread.error_signal.connect(self.window.go_back)
        self.thread.success_signal.connect(partial(self._notify, "success"))
        self.thread.input_update.connect(self.set_expected_input_state)

        self.button_maps = {}
        for name, button_map in [("LEFT", JoystickLeftButtonMap), ("RIGHT", JoystickRightButtonMap), ("TRIGGERS", JoystickTriggersButtonMap)]:
            self.button_maps[name] = button_map(name, self.thread)

        self.thread.start()

    def _notify(self, type, msg):
        self.window.notify(msg, type)
    
    @Slot(tuple)
    def set_expected_input_state(self, input_state):
        self.pressed_expected_input = input_state

    def is_expected_input_pressed(self):
        return self.pressed_expected_input

    def is_joystick_connected(self):
        is_connected = self.thread.is_joystick_connected()
        if not is_connected:
            self._notify("error", "No joystick connected")
        return is_connected

    def set_current_button_map(self, button_map_name):
        self.current_button_map = self.button_maps.get(button_map_name, None)

    def listens_for(self, joystick_input):
        self.thread.set_expected_input_in_map(joystick_input, self.current_button_map)

    # Buttons related methods
    def get_map_names(self):
        return list(self.button_maps.keys())
    
    def get_button_sections_for(self, map_name):
        button_map = self.button_maps.get(map_name, None)
        if self.button_maps:
            return [button_map.get_buttons(), button_map.get_sticks(), button_map.get_dpads(), button_map.get_combos()]
        return []

    def close(self):
        self.thread.stop()
        self.set_expected_input_state(False)
        self.set_current_button_map(None)