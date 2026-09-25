import os

# Hide warnings
os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'
os.environ["QT_LOGGING_RULES"] = "*.warning=false;qt.qpa.fonts.warning=false"

import cv2
from joystick_handler import JoystickHandler
from camera_system import CameraSystem


class Collector:
    def __init__(self, save_dir="./data"):
        self.joystick_handler = JoystickHandler(self._process_inputs)
        self.camera_system = CameraSystem()
        self.save_dir = save_dir
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
            print(filename)
        # self.camera_system.save_frame(filename)

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
    collector = Collector()
    collector.run()