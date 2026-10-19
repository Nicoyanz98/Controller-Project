import os

# Hide warnings
os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'
os.environ["QT_LOGGING_RULES"] = "*.warning=false;qt.qpa.fonts.warning=false"
import cv2
import argparse

from joystick_handler import JoystickHandler
from camera_system import CameraSystem
from clip_recorder import ClipLogic, ClipRecorder

# Label used for frames without any pressed input
IDLE_LABEL = "basura"


class Collector:
    """Records short labeled clips of the controller use, toggled with Start/Select."""

    def __init__(self, save_dir, no_press_timeout, tail, continue_time, max_duration, fps, mjpg):
        self.joystick_handler = JoystickHandler(self._process_inputs)
        self.camera_system = CameraSystem(fps, mjpg)
        self.requested_fps = fps

        try:
            folder_count = len(os.listdir(save_dir))
        except FileNotFoundError:
            folder_count = 0
        self.save_dir = os.path.join(save_dir, str(folder_count))
        os.makedirs(self.save_dir, exist_ok=True)

        self.clip_logic = ClipLogic(no_press_timeout, tail, continue_time, max_duration)
        self.recorder = None
        self.recording_count = 0
        self.saved_count = 0
        self.fps = None
        self.size = None

        self.started = False

    def _process_inputs(self, t, toggle_pressed, inputs):
        """Joystick callback: drives the clip logic and labels the clip being recorded."""
        if not self.started:
            return

        action = self.clip_logic.update(t, toggle_pressed, bool(inputs))
        if action == "start":
            print("Recording started")
            self._open_clip(self.clip_logic.t0)
        elif action in ("save", "discard"):
            self._end_clip(action)

        if self.recorder is not None:
            self.recorder.add_label(t, self._label_from_inputs(inputs))

    def _label_from_inputs(self, inputs):
        """Builds a label like "a" or "combo_a_left_stick_up" from the pressed inputs."""
        if not inputs:
            return IDLE_LABEL

        inputs_list = []
        for input_name, value in inputs.items():
            inputs_list.append((input_name.lower() + "_" + value.lower()).rstrip("_"))
        label = "_".join(sorted(inputs_list))

        if len(inputs) > 1:
            label = "combo_" + label
        return label

    def _open_clip(self, t0):
        """Creates a recorder for a new clip and sends the camera frames to it."""
        self.recording_count += 1
        path = os.path.join(self.save_dir, f"recording_{self.recording_count}.mp4")
        self.recorder = ClipRecorder(path, self.fps, self.size, t0)
        self.camera_system.set_sink(self.recorder.push)

    def _end_clip(self, action):
        """Saves or deletes the finished clip. The next clip is opened first so no frames are lost while saving."""
        finished = self.recorder
        if self.clip_logic.recording:
            self._open_clip(self.clip_logic.t0)
        else:
            self.recorder = None
            self.camera_system.set_sink(None)

        finished.close(self.clip_logic.stop_t)
        if action == "save" and finished.frame_times:
            self.saved_count += 1
            path = os.path.join(self.save_dir, f"clip_{self.saved_count:04d}.mp4")
            finished.save(path)
            print(f"Saved clip to {path} ({len(finished.frame_times)} frames, {self.clip_logic.reason})")
        else:
            finished.delete()

        if not self.clip_logic.recording:
            print(f"Recording stopped ({self.clip_logic.reason}). Press Start or Select to record again")

    def _draw_status(self, frame):
        """Overlays the recorder state on the preview."""
        if self.clip_logic.recording:
            text = f"REC  saved {self.saved_count}"
            color = (0, 0, 255)
        else:
            text = f"IDLE  saved {self.saved_count}"
            color = (0, 200, 0)
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    def run(self):
        try:
            self.joystick_handler.start()
            self.camera_system.start()
            self.fps, self.size = self.camera_system.measure_fps()
            print(f"Camera running at {self.fps:.1f} fps ({self.size[0]}x{self.size[1]})")
            if abs(self.fps - self.requested_fps) > 0.2 * self.requested_fps:
                print(f"Warning: requested {self.requested_fps} fps, got {self.fps:.1f}. Try --mjpg")

            self.started = True
            print("Press Start or Select to start/stop recording, q to quit")
            while True:
                if (frame := self.camera_system.get_frame()) is not None:
                    self._draw_status(frame)
                    cv2.imshow("Camera Feed", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            self.started = False
            self.joystick_handler.stop()

            # A clip in progress is discarded on quit
            if self.recorder is not None:
                self.camera_system.set_sink(None)
                self.recorder.close(self.recorder.t0)
                self.recorder.delete()

            self.camera_system.stop()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collector script.")
    parser.add_argument("--save_dir", default="./data", help="Saving directory for clips obtained")
    parser.add_argument("--t_no_input", default=2.0, help="Seconds to wait for an input after Start/Select before stopping")
    parser.add_argument("--t_tail", default=0.5, help="Seconds kept in a clip after the last input is released")
    parser.add_argument("--t_continue", default=1.5, help="Seconds to keep recording after a clip is saved, waiting for a new input")
    parser.add_argument("--t_max", default=10.0, help="Maximum clip duration in seconds")
    parser.add_argument("--fps", default=30.0, help="Camera fps requested for the clips")
    parser.add_argument("--mjpg", action="store_true", help="Request MJPG from the camera (often needed for 60 fps)")

    args = parser.parse_args()

    collector = Collector(args.save_dir, float(args.t_no_input), float(args.t_tail), float(args.t_continue), float(args.t_max), float(args.fps), args.mjpg)
    collector.run()
