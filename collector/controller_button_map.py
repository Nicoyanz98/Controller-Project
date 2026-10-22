from abc import ABC, abstractmethod
import pygame

AXIS_MAX = 32767.0
STICK_THRESHOLD = 0.5
TRIGGER_THRESHOLD = 0.5

# Directions of the sticks and dpad. Diagonals are their own input (one thumb action),
# not a conflict of two directions
DIRECTIONS = ["up", "down", "left", "right", "up_left", "up_right", "down_left", "down_right"]

def _directional_inputs(prefix, group):
    """Inputs of every direction of a stick or dpad, e.g. "ls_up", "ls_up_left"."""
    inputs = {}
    for direction in DIRECTIONS:
        inputs[f"{prefix}_{direction}"] = group
    return inputs

# Labeled inputs (SDL names, on a PlayStation pad "a" = Cross) and the controller
# part (head group) that presses them. Same names and groups as video_analysis.
INPUT_GROUPS = {
    **_directional_inputs("dpad", "left"),
    "l3": "left",
    "a": "right",
    "b": "right",
    "x": "right",
    "y": "right",
    "r3": "right",
    "lb": "trig_L",
    "lt": "trig_L",
    "rb": "trig_R",
    "rt": "trig_R",
    **_directional_inputs("ls", "left"),
    **_directional_inputs("rs", "right"),
}
LABEL_GROUPS = list(dict.fromkeys(INPUT_GROUPS.values()))
AXIS_NAMES = ["leftx", "lefty", "rightx", "righty", "triggerleft", "triggerright"]

def create_map(type, controller):
    if any(name in type for name in ("playstation", "ps4", "ps5", "dualshock", "dualsense")):
        return PlaystationButtonMap(controller)
    return XboxButtonMap(controller)

def group_labels(pressed):
    """Label per group: "none", the pressed input (e.g. "a") or "conflict:a+b" when
    two inputs of the same group are pressed together."""
    labels = {}
    for group in LABEL_GROUPS:
        group_pressed = [name for name, input_group in INPUT_GROUPS.items() if input_group == group and name in pressed]
        if not group_pressed:
            labels[group] = "none"
        elif len(group_pressed) == 1:
            labels[group] = group_pressed[0]
        else:
            labels[group] = "conflict:" + "+".join(group_pressed)
    return labels

class ControllerButtonMap(ABC):
    """Turns controller events into the set of pressed labeled inputs and the normalized axis values."""

    def __init__(self, controller):
        self.controller = controller
        self._init_map()

        self._event_handlers = {
            pygame.CONTROLLERBUTTONDOWN: (self._handle_button, lambda e: (e.button, True)),
            pygame.CONTROLLERBUTTONUP: (self._handle_button, lambda e: (e.button, False)),
            pygame.CONTROLLERAXISMOTION: (self._handle_axis, lambda e: (e.axis, e.value)),
        }

        self.pressed = set()
        self.axis_values = {name: 0.0 for name in AXIS_NAMES}
        self.stick_values = {"ls": [0.0, 0.0], "rs": [0.0, 0.0]}
        self.dpad_pressed = set()

    def _init_map(self):
        self._init_display_names()
        self._init_inputs()

    @abstractmethod
    def _init_display_names(self):
        """Controller specific names of the labeled inputs, shown in the preview."""
        pass

    def _init_inputs(self):
        self.button = {
            pygame.CONTROLLER_BUTTON_A: "a",
            pygame.CONTROLLER_BUTTON_B: "b",
            pygame.CONTROLLER_BUTTON_X: "x",
            pygame.CONTROLLER_BUTTON_Y: "y",
            pygame.CONTROLLER_BUTTON_LEFTSTICK: "l3",
            pygame.CONTROLLER_BUTTON_RIGHTSTICK: "r3",
            pygame.CONTROLLER_BUTTON_LEFTSHOULDER: "lb",
            pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: "rb",
        }
        # (x, y) of each dpad button, y points up
        self.dpad = {
            pygame.CONTROLLER_BUTTON_DPAD_UP: (0, 1),
            pygame.CONTROLLER_BUTTON_DPAD_DOWN: (0, -1),
            pygame.CONTROLLER_BUTTON_DPAD_LEFT: (-1, 0),
            pygame.CONTROLLER_BUTTON_DPAD_RIGHT: (1, 0),
        }
        self.trigger = {
            pygame.CONTROLLER_AXIS_TRIGGERLEFT: "lt",
            pygame.CONTROLLER_AXIS_TRIGGERRIGHT: "rt",
        }
        # (stick, axis index) of each stick axis
        self.sticks = {
            pygame.CONTROLLER_AXIS_LEFTX: ("ls", 0),
            pygame.CONTROLLER_AXIS_LEFTY: ("ls", 1),
            pygame.CONTROLLER_AXIS_RIGHTX: ("rs", 0),
            pygame.CONTROLLER_AXIS_RIGHTY: ("rs", 1),
        }
        self.axis_names = {
            pygame.CONTROLLER_AXIS_LEFTX: "leftx",
            pygame.CONTROLLER_AXIS_LEFTY: "lefty",
            pygame.CONTROLLER_AXIS_RIGHTX: "rightx",
            pygame.CONTROLLER_AXIS_RIGHTY: "righty",
            pygame.CONTROLLER_AXIS_TRIGGERLEFT: "triggerleft",
            pygame.CONTROLLER_AXIS_TRIGGERRIGHT: "triggerright",
        }
        # Start/Select control the recorder and are never used as labels
        self.toggle_buttons = {
            pygame.CONTROLLER_BUTTON_START: "start",
            pygame.CONTROLLER_BUTTON_BACK: "back",
        }

    def toggle_name(self, event):
        """Name of the Start/Select button ("start" or "back") of the event, None for other events."""
        is_button_event = event.type in (pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLERBUTTONUP)
        if is_button_event:
            return self.toggle_buttons.get(event.button)
        return None

    def display_name(self, name):
        return self.display_names.get(name, name)

    def axes(self):
        """Normalized axis values (-1..1, triggers 0..1) in AXIS_NAMES order."""
        return tuple(self.axis_values[name] for name in AXIS_NAMES)

    def handle_event(self, event):
        handler, get_args = self._event_handlers.get(event.type, (None, None))
        if handler:
            handler(*get_args(event))

    def _handle_button(self, button, pressed):
        if button in self.dpad:
            self._update_dpad(button, pressed)
            return

        name = self.button.get(button)
        if name is None:
            return
        if pressed:
            self.pressed.add(name)
        else:
            self.pressed.discard(name)

    def _handle_axis(self, axis, value):
        value = max(-1.0, min(1.0, value / AXIS_MAX))
        if axis in self.axis_names:
            self.axis_values[self.axis_names[axis]] = value

        if axis in self.trigger:
            name = self.trigger[axis]
            if value > TRIGGER_THRESHOLD:
                self.pressed.add(name)
            else:
                self.pressed.discard(name)

        if axis in self.sticks:
            stick, index = self.sticks[axis]
            self.stick_values[stick][index] = value
            self._update_stick(stick)

    def _update_dpad(self, button, pressed):
        if pressed:
            self.dpad_pressed.add(button)
        else:
            self.dpad_pressed.discard(button)

        x = sum(self.dpad[dpad_button][0] for dpad_button in self.dpad_pressed)
        y = sum(self.dpad[dpad_button][1] for dpad_button in self.dpad_pressed)
        self._set_direction("dpad", x, y)

    def _update_stick(self, stick):
        """Each stick axis past STICK_THRESHOLD adds its direction, both of them make a diagonal."""
        x, y = self.stick_values[stick]
        x_direction = 1 if x > STICK_THRESHOLD else -1 if x < -STICK_THRESHOLD else 0
        # SDL's y axis points down
        y_direction = -1 if y > STICK_THRESHOLD else 1 if y < -STICK_THRESHOLD else 0
        self._set_direction(stick, x_direction, y_direction)

    def _set_direction(self, prefix, x, y):
        """Presses the input of the (x, y) direction (-1/0/1, y up) and releases the others of prefix."""
        for direction in DIRECTIONS:
            self.pressed.discard(f"{prefix}_{direction}")

        parts = []
        if y > 0:
            parts.append("up")
        elif y < 0:
            parts.append("down")
        if x < 0:
            parts.append("left")
        elif x > 0:
            parts.append("right")

        if parts:
            self.pressed.add(f"{prefix}_{'_'.join(parts)}")

class XboxButtonMap(ControllerButtonMap):
    def _init_display_names(self):
        self.display_names = {
            "a": "A",
            "b": "B",
            "x": "X",
            "y": "Y",
            "lb": "LB",
            "rb": "RB",
            "lt": "LT",
            "rt": "RT",
        }

class PlaystationButtonMap(ControllerButtonMap):
    def _init_display_names(self):
        self.display_names = {
            "a": "Cross",
            "b": "Circle",
            "x": "Square",
            "y": "Triangle",
            "lb": "L1",
            "rb": "R1",
            "lt": "L2",
            "rt": "R2",
        }
