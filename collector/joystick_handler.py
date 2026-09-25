import pygame
from time import sleep, time
import threading

from controller_button_map import create_map

class JoystickHandler:
    def __init__(self, callback, wait_input_time, wait_idle_time):
        self.callback = callback
        self.wait_input_time = wait_input_time
        self.wait_idle_time = wait_idle_time
        
        pygame.init()

        self.joystick_handler = pygame.joystick
        self.joystick_handler.init()

        self._init_joystick()

        self.button_map = create_map(self.joystick.get_name().lower(), self.joystick)

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
        print("Controller detected")
        self.joystick = self.joystick_handler.Joystick(0)

    def _worker(self):
        last_time_pressed = time()
        while self.running:
            self._handle_inputs()

            elapsed_time = time() - last_time_pressed
            if (self.pressed_input and elapsed_time > self.wait_input_time) or (not self.pressed_input and elapsed_time > self.wait_idle_time):
                last_time_pressed = time()
                self.callback(self.pressed_input)
                    

    def _handle_inputs(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            name, value, is_active = self.button_map.handle_event(event)

            if name is not None:
                if is_active:
                    self.pressed_input[name] = value
                else:
                    self.pressed_input.pop(name, None)

        pygame.event.pump()

    def start(self):
        self.running = True
        self.joystick_thread.start()

    def stop(self):
        self.running = False
        self.joystick_thread.join()
        pygame.quit()