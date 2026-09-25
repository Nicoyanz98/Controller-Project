from abc import ABC, abstractmethod

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