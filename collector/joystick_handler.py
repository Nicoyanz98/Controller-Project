import pygame
from pygame._sdl2 import controller
from time import sleep, perf_counter
import threading

from controller_button_map import create_map

class JoystickHandler:
    """Polls the controller on its own thread and reports its state through
    callback(t, toggle_pressed, pressed_input) on every poll."""

    def __init__(self, callback):
        self.callback = callback

        pygame.init()

        self.joystick_handler = controller
        self.joystick_handler.init()

        self._init_joystick()

        self.button_map = create_map(self.joystick.name.lower(), self.joystick)

        self.pressed_input = {}

        self.joystick_thread = threading.Thread(target=self._worker, daemon=True)

    def _init_joystick(self):
        warned = False
        while self.joystick_handler.get_count() <= 0:
            if not warned:
                print("Please connect a controller")
                warned = True
            pygame.event.pump()
            sleep(1)
        if not self.joystick_handler.is_controller(0):
            raise RuntimeError("Controller not recognized by SDL's controller database")
        self.joystick = self.joystick_handler.Controller(0)
        print(f"Controller detected: {self.joystick.name}")

    def _worker(self):
        while self.running:
            toggle_pressed = self._handle_inputs()
            self.callback(perf_counter(), toggle_pressed, self.pressed_input)
            sleep(0.001)

    def _handle_inputs(self):
        """Updates pressed_input and returns True if Start/Select was just pressed."""
        toggle_pressed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return toggle_pressed

            if self.button_map.is_toggle_button(event):
                if event.type == pygame.CONTROLLERBUTTONDOWN:
                    toggle_pressed = True
                continue

            name, value, is_active = self.button_map.handle_event(event)

            if name is not None:
                if is_active:
                    self.pressed_input[name] = value
                else:
                    self.pressed_input.pop(name, None)

        pygame.event.pump()
        return toggle_pressed

    def start(self):
        self.running = True
        self.joystick_thread.start()

    def stop(self):
        self.running = False
        self.joystick_thread.join()
        pygame.quit()
