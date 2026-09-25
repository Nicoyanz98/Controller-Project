from abc import ABC, abstractmethod
import pygame

def create_map(type, controller):
    if "playstation" in type and "4" in type:
        return Playstation4ButtonMap(controller)
    elif "playstation" in type and "5" in type:
        return Playstation5ButtonMap(controller)
    elif "xbox" in type:
        return XboxButtonMap(controller)
    else:
        raise ValueError("Invalid controller type. Must be 0 (Playstation) or 1 (Xbox).")

class ControllerButtonMap(ABC):
    def __init__(self, controller):
        self.controller = controller
        self._init_map()

        self._event_handlers = {
            pygame.JOYBUTTONDOWN: (self._handle_button, lambda e: (e.button, True)),
            pygame.JOYBUTTONUP: (self._handle_button, lambda e: (e.button, False)),
            pygame.JOYAXISMOTION: (self._handle_axis, lambda e: (e.axis, e.value)),
            pygame.JOYHATMOTION: (self._handle_hat, lambda e: (e.hat, e.value)),
        }

        self.axis_value = (0, 0)

    @abstractmethod
    def _init_map(self):
        pass

    def axis(self):
        return self.axis

    def button(self):
        return self.button

    def handle_event(self, event):
        handler, get_args = self._event_handlers.get(event.type, (None, None))
        if handler:
            return handler(*get_args(event))
        return None, None, None

    def _handle_button(self, button, pressed):
        if button in self.button:
            return self.button[button], "", pressed
        else:
            return f"Unknown Button {button}", None, None

    def _handle_hat(self, hat, value):
        x, y = value
        is_active = (x + y) != 0
        if hat in self.hat:
            return f"{self.hat[hat]}", self._convert_directional_input(value), is_active
        else:
            return f"Unknown Hat {hat}", None, None

    def _handle_axis(self, axis, value):
        if axis in self.axis:
            stick_name, axis_name = self._get_stick_and_axis_name(axis)
            self._update_axis_value(value, axis_name)
            is_active = self.axis_value != (0,0)

            return stick_name, self._convert_directional_input(self.axis_value), is_active
        else:
            return f"Unknown Axis {axis}", None, None

    def _convert_directional_input(self, value):
        x, y = value
        directions = []
        if y == 1:
            directions.append("Up")
        elif y == -1:
            directions.append("Down")
        
        if x == -1:
            directions.append("Left")
        elif x == 1:
            directions.append("Right")

        if directions:
            return "_".join(directions)
        
        return "Idle"

    def _get_stick_and_axis_name(self, axis):
        _splits = self.axis[axis].split(" ")
        name = "_".join(_splits[:2])
        return name, _splits[-1]
            
    def _update_axis_value(self, value, axis_name):
        x, y = self.axis_value
        value = 1 if value > 0.5 else -1 if value < -0.5 else 0
        if "Horizontal" == axis_name:
            x = value
        else:
            y = value
        self.axis_value = (x, y)
        
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
            0: "DPad",
        }

class Playstation4ButtonMap(ControllerButtonMap):
    def _init_(self, controller):
        super().__init__(controller)
        self.hat_value = (0,0)

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
            11: "DPad Up",
            12: "DPad Down",
            13: "DPad Left",
            14: "DPad Right"
        }

    def _handle_button(self, button, pressed):
        if not button in self.hat:
            super()._handle_button(button, pressed)
        
        name, value = self.hat[button].split(" ")

        self._update_hat_value(button, pressed, value)
        
        return name, self._convert_directional_input(self.hat_value), pressed

    def _update_hat_value(self, button, pressed, value):
        x, y = self.hat_value
        direction  = (-1) ** (int(not pressed))
        if (button % 10) < 3:
            y += direction * (1 if value == "Up" else -1)
        else:
            x += direction * (1 if value == "Right" else -1)
        self.hat_value = x, y
            

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
            0: "DPad",
        }