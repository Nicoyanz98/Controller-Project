import pygame
from components.tasks.thread_task import Thread_Task
from PySide6.QtCore import Signal

class JoystickThread(Thread_Task):
    def __init__(self, window, name, button_map_name):
        self.window = window
        self.button_map_name = button_map_name
        super().__init__(window, name)
        pygame.init()

    def run(self):
        while self._run_flag:
            self.window.update_current_input(self.button_map_name)
            self.msleep(10)

   