import pygame
from time import sleep, time
import threading

from controller_button_map import create_map

class JoystickHandler:
    def __init__(self, callback):
        self.callback = callback
        
        pygame.init()

        self.joystick_handler = pygame.joystick
        self.joystick_handler.init()

        self._init_joystick()

        self.button_map = create_map(self.joystick.get_name().lower(), self.joystick)

        self.axis_motion = set()
        self.pressed_input = set()

        self.joystick_thread = threading.Thread(target=self._worker, daemon=True)

    def _init_joystick(self):
        while not self.joystick_handler.get_count() > 0:
            sleep(1)
        self.joystick = self.joystick_handler.Joystick(0)

    def _worker(self):
        last_time_pressed = time()
        while self.running:
            self._handle_inputs()

            if self.pressed_input:
                last_time_pressed = time()
                self.callback(self.pressed_input)
            else:
                elapsed_time = time() - last_time_pressed
                if elapsed_time >= 4.0:
                    last_time_pressed = time()
                    self.callback(self.pressed_input)
                    

    def _handle_inputs(self, callback_fn=None):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if event.type == pygame.JOYBUTTONDOWN:
                self.pressed_input.add(self.button_map.handle_button(event.button))
            elif event.type == pygame.JOYBUTTONUP:
                self.pressed_input.discard(self.button_map.handle_button(event.button))

            elif event.type == pygame.JOYAXISMOTION:
                if abs(event.value) > 0.5:
                    self.pressed_input.add(self.button_map.handle_axis(event.axis, event.value))
                    self.axis_motion.add(event.axis)
                elif abs(event.value) <= 0.5 and event.axis in self.axis_motion:
                    self.pressed_input.discard(self.button_map.handle_axis(event.axis, event.value))
                    self.axis_motion.remove(event.axis)

            elif event.type == pygame.JOYHATMOTION:
                x, y = event.value
                if abs(x) == 1 or abs(y) == 1:
                    self.pressed_input.add(self.button_map.handle_hat(event.hat, event.value))
                else:
                    self.pressed_input.discard(self.button_map.handle_hat(event.hat, event.value))
        
        if callback_fn:
            callback_fn(self.pressed_input)
        pygame.event.pump()

    def start(self):
        self.running = True
        self.joystick_thread.start()

    def stop(self):
        self.running = False
        self.joystick_thread.join()
        pygame.quit()