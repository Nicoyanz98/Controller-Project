import os

# Hide warnings
os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'
os.environ["QT_LOGGING_RULES"] = "*.warning=false;qt.qpa.fonts.warning=false"
import cv2
import argparse

from joystick_handler import JoystickHandler
from camera_system import CameraSystem


class Collector:
    def __init__(self, save_dir, wait_input, wait_idle):
        self.joystick_handler = JoystickHandler(self._process_inputs, wait_input, wait_idle)
        self.camera_system = CameraSystem()
        
        try:
            folder_count = len(os.listdir(save_dir))
        except FileNotFoundError:
            folder_count = 0
        self.save_dir = os.path.join(save_dir, str(folder_count))
        os.makedirs(self.save_dir, exist_ok=True)
        
        self.started = False

    def _process_inputs(self, inputs):
        if self.started:
            name = "basura"
            if inputs:
                is_combo = len(inputs.keys()) > 1
                inputs_list = [(input_name.lower() + "_" + value.lower()).rstrip("_") for input_name, value in inputs.items()]
                ordered_inputs = sorted(inputs_list)
                name = "_".join(ordered_inputs)
                if is_combo:
                    name = "combo_" + name
            filename = os.path.join(self.save_dir, name)
            self.camera_system.save_frame(filename)

    def run(self):
        try:
            self.joystick_handler.start()
            self.camera_system.start()
            
            self.started = True

            self.joystick_handler.start
            while True:
                if (frame := self.camera_system.get_frame()) is not None:
                    cv2.imshow("Camera Feed", frame)
    
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            self.joystick_handler.stop()
            self.camera_system.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collector script.")
    parser.add_argument("--save_dir", default="./data", help="Saving directory for images obtained")
    parser.add_argument("--t_input", default=1.0, help="Waiting time (in seconds) to capture image between continuos inputs")
    parser.add_argument("--t_idle", default=5.0, help="Waiting time (in seconds) to capture image while idle")

    args = parser.parse_args()

    collector = Collector(args.save_dir, float(args.t_input), float(args.t_idle))
    collector.run()