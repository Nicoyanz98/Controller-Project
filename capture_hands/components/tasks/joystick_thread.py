import pygame
from components.tasks.thread_task import Thread_Task
from PySide6.QtCore import Signal

class JoystickThread(Thread_Task):
    def __init__(self, window, name):
        self.window = window
        super().__init__(window, name)
        pygame.init()

    def run(self):
        while self._run_flag:
            self.window.get_current_input()
            self.msleep(10)

   