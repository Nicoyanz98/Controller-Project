import pygame
from pygame._sdl2 import controller
from time import sleep, perf_counter
import threading

from controller_button_map import create_map

class JoystickHandler:
    """
    Polls the controller on its own thread and reports its state through
    callback(t, toggle, pressed, axes) on every poll:

    Inputs handling:
        toggle -> "start"/"back" when Start/Select was just pressed, None otherwise
        pressed -> frozenset of the pressed labeled inputs (e.g. {"a", "ls_up"})
        axes -> normalized axis values, in controller_button_map.AXIS_NAMES order
    """

    def __init__(self, callback):
        self.callback = callback

        pygame.init()

        self.joystick_handler = controller
        self.joystick_handler.init()

        self._init_joystick()

        self.button_map = create_map(self.joystick.name.lower(), self.joystick)

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
            toggle = self._handle_inputs()
            self.callback(perf_counter(), toggle, frozenset(self.button_map.pressed), self.button_map.axes())
            sleep(0.001)

    def _handle_inputs(self):
        """Updates the controller state and returns the Start/Select button just pressed, if any."""
        toggle = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return toggle

            toggle_name = self.button_map.toggle_name(event)
            if toggle_name is not None:
                if event.type == pygame.CONTROLLERBUTTONDOWN:
                    toggle = toggle_name
                continue

            self.button_map.handle_event(event)

        pygame.event.pump()
        return toggle

    def start(self):
        self.running = True
        self.joystick_thread.start()

    def stop(self):
        self.running = False
        self.joystick_thread.join()
        pygame.quit()
