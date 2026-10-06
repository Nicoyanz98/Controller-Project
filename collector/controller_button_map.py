from abc import ABC, abstractmethod
import pygame

STICK_THRESHOLD = 16384
TRIGGER_THRESHOLD = 16384

def create_map(type, controller):
    if any(name in type for name in ("playstation", "ps4", "ps5", "dualshock", "dualsense")):
        return PlaystationButtonMap(controller)
    return XboxButtonMap(controller)

class ControllerButtonMap(ABC):
    def __init__(self, controller):
        self.controller = controller
        self._init_map()

        self._event_handlers = {
            pygame.CONTROLLERBUTTONDOWN: (self._handle_button, lambda e: (e.button, True)),
            pygame.CONTROLLERBUTTONUP: (self._handle_button, lambda e: (e.button, False)),
            pygame.CONTROLLERAXISMOTION: (self._handle_axis, lambda e: (e.axis, e.value)),
            # pygame.JOYHATMOTION: (self._handle_hat, lambda e: (e.hat, e.value)),
        }

        self.axis_values = {}
        self.dpad_pressed = set()

    
    def _init_map(self):
        self._init_buttons_and_triggers()
        self._init_sticks_and_dpad()
    
    @abstractmethod
    def _init_buttons_and_triggers(self):
        pass

    def _init_sticks_and_dpad(self):
        self.dpad = {
            pygame.CONTROLLER_BUTTON_DPAD_UP: (0, 1),
            pygame.CONTROLLER_BUTTON_DPAD_DOWN: (0, -1),
            pygame.CONTROLLER_BUTTON_DPAD_LEFT: (-1, 0),
            pygame.CONTROLLER_BUTTON_DPAD_RIGHT: (1, 0),
        }
        self.sticks = {
            pygame.CONTROLLER_AXIS_LEFTX: ("Left_Stick", "Horizontal"),
            pygame.CONTROLLER_AXIS_LEFTY: ("Left_Stick", "Vertical"),
            pygame.CONTROLLER_AXIS_RIGHTX: ("Right_Stick", "Horizontal"),
            pygame.CONTROLLER_AXIS_RIGHTY: ("Right_Stick", "Vertical"),
        }

    def handle_event(self, event):
        handler, get_args = self._event_handlers.get(event.type, (None, None))
        if handler:
            return handler(*get_args(event))
        return None, None, None

    def _handle_button(self, button, pressed):
        if button in self.dpad:
            return self._handle_dpad(button, pressed)
        if button in self.button:
            return self.button[button], "", pressed
        
        return f"Unknown Button {button}", None, None

    def _handle_dpad(self, button, pressed):
        if pressed:
            self.dpad_pressed.add(button)
        else:
            self.dpad_pressed.discard(button)
        x = sum(self.dpad[dpad][0] for dpad in self.dpad_pressed)
        y = sum(self.dpad[dpad][1] for dpad in self.dpad_pressed)
        is_active = (x, y) != (0, 0)

        return "DPad", self._convert_directional_input((x, y)), is_active

    def _handle_axis(self, axis, value):
        if axis in self.trigger:
            return self.trigger[axis], "", value > TRIGGER_THRESHOLD
        
        if axis in self.sticks:
            stick_name, axis_name = self.sticks[axis]
            self._update_axis_value(stick_name, value, axis_name)
            is_active = self.axis_values[stick_name] != (0,0)
            return stick_name, self._convert_directional_input(self.axis_values[stick_name]), is_active
            
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

    def _update_axis_value(self, stick_name, value, axis_name):
        x, y = self.axis_values.get(stick_name, (0, 0))
        v = 1 if value > STICK_THRESHOLD else -1 if value < -STICK_THRESHOLD else 0
        if axis_name == "Horizontal":
            x = v
        else:
            y = -v
        self.axis_values[stick_name] = (x, y)
        
class XboxButtonMap(ControllerButtonMap):
    def _init_buttons_and_triggers(self):
        self.button = {
            pygame.CONTROLLER_BUTTON_A: "A",
            pygame.CONTROLLER_BUTTON_B: "B",
            pygame.CONTROLLER_BUTTON_X: "X",
            pygame.CONTROLLER_BUTTON_Y: "Y",
            pygame.CONTROLLER_BUTTON_LEFTSHOULDER: "Left_Bumper",
            pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: "Right_Bumper"
        }
        self.trigger = {
            pygame.CONTROLLER_AXIS_TRIGGERLEFT: "Left_Trigger",
            pygame.CONTROLLER_AXIS_TRIGGERRIGHT: "Right_Trigger"
        }
        super()._init_sticks_and_dpad()

class PlaystationButtonMap(ControllerButtonMap):
    def _init_buttons_and_triggers(self):
        self.button = {
            pygame.CONTROLLER_BUTTON_A: "Cross",
            pygame.CONTROLLER_BUTTON_B: "Circle",
            pygame.CONTROLLER_BUTTON_X: "Square",
            pygame.CONTROLLER_BUTTON_Y: "Triangle",
            pygame.CONTROLLER_BUTTON_LEFTSHOULDER: "L1",
            pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: "R1"
        }
        self.trigger = { # Button indexes for the D-Pad on a PS4 controller
            pygame.CONTROLLER_AXIS_TRIGGERLEFT: "L2",
            pygame.CONTROLLER_AXIS_TRIGGERRIGHT: "R2"
        }
        super()._init_sticks_and_dpad()