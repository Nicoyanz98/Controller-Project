import pygame
from components.tasks.thread_task import Thread_Task
from PySide6.QtCore import Signal

class JoystickThread(Thread_Task):
    buttons_intialized = Signal()
    TRIGGER_THRESHOLD = 0.5
    STICK_THRESHOLD = 0.2

    def __init__(self, parent, name, buttons_map):
        super().__init__(parent, name)
        pygame.init()
        self.buttons_map = buttons_map
        self.expected_input = None
        self.pressed_expected_input = False

    def run(self):
        self._init_joystick()

        if not hasattr(self, "joystick"):
            return

        while self._run_flag:
            pygame.event.pump()
            if self.expected_input:
                self._check_active_input()
            self.msleep(10)

    def _check_active_input(self):
        self.buttons_map.resolve_input(self.expected_input)

    def listen_for(self, expected_input):
        self.expected_input = expected_input
    
    def get_button(self, button_index):
        self.pressed_expected_input = self.joystick.get_button(button_index)

    def get_stick(self, stick_axis, direction):        
        x_axis, y_axis = stick_axis
        x, y = self.joystick.get_axis(x_axis), self.joystick.get_axis(y_axis)
        
        get_direction = lambda value: 0 if abs(value) < self.STICK_THRESHOLD else (1 if value > 0 else -1)
        x_dir, y_dir = get_direction(x), get_direction(y)

        self.pressed_expected_input = (x_dir, y_dir) == direction

    def get_dpad(self, direction):
        self.pressed_expected_input = self.joystick.get_hat(0) == direction

    def get_trigger(self, trigger_axis):
        self.pressed_expected_input = self.joystick.get_axis(trigger_axis) > self.TRIGGER_THRESHOLD

    def is_expected_input_pressed(self):
        return self.pressed_expected_input

    def _init_joystick(self):
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            name = self.joystick.get_name()
            self.buttons_map.init_map(self, is_xbox_type=("xbox" in name.lower()))
            self.buttons_intialized.emit()

            self.success_signal.emit(f"Joystick connected: {name}")
        else:
            self.error_signal.emit("No joystick connected")