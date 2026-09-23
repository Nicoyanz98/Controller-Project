import pygame
from time import sleep
from abc import ABC, abstractmethod

class ControllerButtonMap(ABC):
    def __init__(self, type, controller):
        if "playstation" in type and "4" in type:
            return Playstation4ButtonMap(controller)
        elif "playstation" in type and "5" in type:
            return Playstation5ButtonMap(controller)
        elif "xbox" in type:
            return XboxButtonMap(controller)
        else:
            raise ValueError("Invalid controller type. Must be 0 (Playstation) or 1 (Xbox).")

    def __init__(self, controller):
        self.controller = controller
        self._init_map()

    @abstractmethod
    def _init_map(self):
        pass

    def axis(self):
        return self.axis

    def button(self):
        return self.button

    def _convert_directional_input(self, value):
        if value == (0, 1):
            return "Up"
        elif value == (0, -1):
            return "Down"
        elif value == (-1, 0):
            return "Left"
        elif value == (1, 0):
            return "Right"
        else:
            return "Idle"

    def _normalize_axis_value(self, axis, value):
        x, y = 0, 0
        value = 1 if value > 0.5 else -1 if value < -0.5 else 0
        if "Horizontal" in self.axis[axis]:
            x = value
        else:
            y = value
            
        return value, x, y

    def handle_axis(self, axis, value):
        value, x, y = self._normalize_axis_value(axis, value)

        if axis in self.axis:
            return f"{self.axis[axis]} ({self._convert_directional_input((x, y))})"
        else:
            return f"Unknown Axis {axis} ({value})"

    def handle_button(self, button):
        if button in self.button:
            return self.button[button]
        else:
            return f"Unknown Button {button}"

    def handle_hat(self, hat, value):
        if hat in self.hat:
            return f"{self.hat[hat]} ({self._convert_directional_input(value)})"
        else:
            return f"Unknown Hat {hat} ({value})"
        
class XboxButtonMap(ControllerButtonMap):
    def _init_map(self):
        self.axis = {
            0: "Left Stick - Horizontal",
            1: "Left Stick - Vertical",
            3: "Right Stick - Horizontal",
            4: "Right Stick - Vertical",
            2: "Left Trigger",
            5: "Right Trigger"
        }
        self.button = {
            0: "A",
            1: "B",
            2: "X",
            3: "Y",
            4: "Left Bumper",
            5: "Right Bumper"
        }
        self.hat = {
            0: "D-Pad",
        }

class Playstation4ButtonMap(ControllerButtonMap):
    def _init_map(self):
        self.axis = {
            0: "Left Stick - Horizontal",
            1: "Left Stick - Vertical",
            2: "Right Stick - Horizontal",
            3: "Right Stick - Vertical",
            4: "L2",
            5: "R2"
        }
        self.button = {
            0: "Cross",
            1: "Square",
            2: "Circle",
            3: "Triangle",
            4: "L1",
            5: "R1"
        }
        self.hat = { # Button indexes for the D-Pad on a PS4 controller
            11: "D-Pad Up",
            12: "D-Pad Down",
            13: "D-Pad Left",
            14: "D-Pad Right"
        }

class Playstation5ButtonMap(ControllerButtonMap):
    def _init_map(self):
        self.axis = {
            0: "Left Stick - Horizontal",
            1: "Left Stick - Vertical",
            3: "Right Stick - Horizontal",
            4: "Right Stick - Vertical",
            2: "L2",
            5: "R2"
        }
        self.button = {
            0: "Cross",
            1: "Square",
            2: "Circle",
            3: "Triangle",
            4: "L1",
            5: "R1"
        }
        self.hat = {
            0: "D-Pad",
        }

class JoystickHandler:
    def __init__(self):
        pygame.init()

        self.joystick_handler = pygame.joystick
        self.joystick_handler.init()

        self._init_joystick()

        self.button_map = ControllerButtonMap(self.joystick.get_name().lower(), self.joystick)

        self.axis_motion = {}

    def _init_joystick(self):
        while self.joystick_handler.get_count() > 0:
            sleep(10)
        self.joystick = self.joystick_handler.Joystick(0)
        self.joystick.init()

    def handle_inputs(self, callback_fn=None):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.JOYBUTTONDOWN:
                if callback_fn:
                    callback_fn(f"{self.button_map.handle_button(event.button)} pressed")
            elif event.type == pygame.JOYBUTTONUP:
                if callback_fn:
                    callback_fn(f"{self.button_map.handle_button(event.button)} released")

            elif event.type == pygame.JOYAXISMOTION:
                if abs(event.value) > 0.5:
                    if callback_fn:
                        callback_fn(f"{self.button_map.handle_axis(event.axis, event.value)} used")
                    self.axis_motion[event.axis] = event.value
                elif abs(event.value) <= 0.5 and self.axis_motion.get(event.axis, False):
                    if callback_fn:
                        callback_fn(f"{self.button_map.handle_axis(event.axis, event.value)} centered")
                    del self.axis_motion[event.axis]

            elif event.type == pygame.JOYHATMOTION:
                x, y = event.value
                if abs(x) == 1 or abs(y) == 1:
                    if callback_fn:
                        callback_fn(f"{self.button_map.handle_hat(event.hat, event.value)} pressed")
                else:
                    if callback_fn:
                        callback_fn(f"{self.button_map.handle_hat(event.hat, event.value)} released")

        pygame.event.pump()