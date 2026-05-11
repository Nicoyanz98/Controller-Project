import pygame
from components.tasks.thread_task import Thread_Task
from PySide6.QtCore import Signal

class JoystickThread(Thread_Task):
    buttons_intialized = Signal()

    def __init__(self, parent, name, buttons_map):
        super().__init__(parent, name)
        pygame.init()
        self.buttons_map = buttons_map

    def run(self):
        self._init_joystick()
        # Hear inputs after being allowed to hear them (timed with the image capture)
        # Save input with current video thread image (use parent as middle-man)

    def _init_joystick(self):
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            name = self.joystick.get_name()
            self.buttons_map.init_map(is_xbox_type=("xbox" in name.lower()))
            self.buttons_intialized.emit()

            self.success_signal.emit(f"Joystick conectado: {name}")
        else:
            self.error_signal.emit("No joystick connected")