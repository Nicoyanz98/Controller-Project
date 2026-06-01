import pygame
from collector.tasks import Thread_Task
from PySide6.QtCore import Signal, QMutex, QMutexLocker

class JoystickThread(Thread_Task):
    TRIGGER_THRESHOLD = 0.5
    STICK_THRESHOLD = 0.2

    input_update = Signal(str)

    def __init__(self, manager, name):
        super().__init__(manager, name)
        pygame.init()
        pygame.joystick.init()

        self.joystick_connected = False
        self.connection_lock = QMutex()
        self.input_lock = QMutex()
        self.set_expected_input_in_map(None, None)

        self._update_joystick_connection()

    def _update_joystick_connection(self):
        with QMutexLocker(self.connection_lock):
            was_connected = self.joystick_connected
            is_connected = self._check_joystick_connection()
            self.joystick_connected = is_connected
        
        if not was_connected and is_connected:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

            name = self.joystick.get_name()
            self.joystick_type = 1 if "xbox" in name.lower() else 0

            self.success_signal.emit(f"Joystick connected: {name}")
        elif was_connected and not is_connected:
            if self.joystick is not None:
                self.error_signal.emit("Joystick disconnected")
            self.joystick = None

    def _check_joystick_connection(self):
        return pygame.joystick.get_count() > 0

    def is_joystick_connected(self):
        with QMutexLocker(self.connection_lock):
            connected = self.joystick_connected
        return connected

    def run(self):
        while self._run_flag:
            with QMutexLocker(self.connection_lock):
                if self.joystick_connected:
                    self.update_expected_input()
            
            self._update_joystick_connection()
                
            self.msleep(10)
    
    def set_expected_input_in_map(self, joystick_input, button_map):
        with QMutexLocker(self.input_lock):
            self.expected_input = joystick_input
            self.current_button_map = button_map

    def update_expected_input(self):
        pygame.event.pump()
        if self.expected_input:
            with QMutexLocker(self.input_lock):
                expected = self.expected_input
                button_map = self.current_button_map
            pressed = button_map.resolve_input(expected, self.joystick_type)
            self.input_update.emit(pressed)
    
    # Buttons handling
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

   