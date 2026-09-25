import os
import threading

from joystick_handler import JoystickHandler
from camera_system import CameraSystem

class Collector:
    def __init__(self, save_dir="./data"):
        self.joystick_handler = JoystickHandler(self._process_inputs)
        self.camera_system = CameraSystem()
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def _process_inputs(self, inputs):
        name = "basura"
        if inputs:
            is_combo = len(inputs.keys()) > 1
            inputs_list = [(input_name.lower() + "_" + value.lower()).rstrip("_") for input_name, value in inputs.items()]
            ordered_inputs = sorted(inputs_list)
            name = "_".join(ordered_inputs)
            if is_combo:
                name = "combo_" + name
        filename = os.path.join(self.save_dir, name)
        print(filename)
        # self.camera_system.save_frame(filename)

    def run(self):
        try:
            self.joystick_handler.start()
            self.camera_system.start()
        finally:
            self.joystick_handler.stop()
            self.camera_system.stop()

if __name__ == "__main__":
    collector = Collector()
    collector.run()