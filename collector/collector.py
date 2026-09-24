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
        file_name = "trash"
        if inputs:
            ordered_inputs = list(inputs).sort()
            file_name = "+".join(ordered_inputs)
        print(file_name)

    def process_frame(self, frame):
        def save_frame(frame, filename):
            filepath = os.path.join(self.save_dir, filename)
            cv2.imwrite(filepath, frame)
            self.camera_system.inform(f"Saved frame to {filepath}")
            

    def run(self):
        self.camera_system.run(callback_fn=self.process_frame)

if __name__ == "__main__":
    collector = Collector()
    collector.run()