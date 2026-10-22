import os

# Hide warnings
os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'
os.environ["QT_LOGGING_RULES"] = "*.warning=false;qt.qpa.fonts.warning=false"
import cv2
import csv
import argparse
from datetime import datetime

from joystick_handler import JoystickHandler
from camera_system import CameraSystem
from clip_recorder import ClipLogic, ClipRecorder
from controller_button_map import INPUT_GROUPS


class Collector:
    """Records short labeled clips of the controller use, toggled with Start/Select."""

    def __init__(self, save_dir, subject, no_press_timeout, tail, continue_time, max_duration, fps, mjpg):
        self.joystick_handler = JoystickHandler(self._process_inputs)
        self.camera_system = CameraSystem(fps, mjpg)
        self.subject = subject
        self.requested_fps = fps

        # One session folder per run
        self.save_dir = os.path.join(save_dir, f"{subject}_{datetime.now():%Y%m%d-%H%M%S}")
        os.makedirs(self.save_dir, exist_ok=True)
        self.index_path = os.path.join(self.save_dir, "index.csv")
        with open(self.index_path, "w", newline="") as f:
            csv.writer(f).writerow(["clip", "duration_s", "n_frames", "pressed_inputs", "end_reason"])

        self.clip_logic = ClipLogic(no_press_timeout, tail, continue_time, max_duration)
        self.recorder = None
        self.recording_count = 0
        self.saved_count = 0
        self.started_by = None
        self.pressed = frozenset()
        self.fps = None
        self.size = None

        self.started = False

    def _process_inputs(self, t, toggle, pressed, axes):
        """Joystick callback: drives the clip logic and stores the controller state of the clip being recorded."""
        self.pressed = pressed
        if not self.started:
            return

        action = self.clip_logic.update(t, toggle, bool(pressed))
        if action == "start":
            print(f"Recording started by {toggle}")
            self.started_by = toggle
            self._open_clip(self.clip_logic.t0)
        elif action in ("save", "discard"):
            self._end_clip(action)

        if self.recorder is not None:
            self.recorder.add_sample(t, pressed, axes)

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
            self._save_clip(finished)
        else:
            finished.delete()

        # Chained clips are not started by a Start/Select press
        self.started_by = "continue"

        if not self.clip_logic.recording:
            print(f"Recording stopped ({self.clip_logic.reason}). Press Start or Select to record again")

    def _save_clip(self, recorder):
        """Saves the clip files (same format as video_analysis) and adds it to the session index."""
        self.saved_count += 1
        clip = f"clip_{self.saved_count:04d}"
        meta = {
            "clip": clip,
            "subject": self.subject,
            "recorded_at": datetime.now().isoformat(timespec="seconds"),
            "controller": self.joystick_handler.joystick.name,
            "started_by": self.started_by,
            "end_reason": self.clip_logic.reason,
            "camera_index": 0,
            "fps_requested": self.requested_fps,
            "fps_measured": round(self.fps, 2),
            "width": self.size[0],
            "height": self.size[1],
            "camera_latency_s": 0.0,
            "no_press_timeout_s": self.clip_logic.no_press_timeout,
            "tail_s": self.clip_logic.tail,
            "continue_s": self.clip_logic.continue_time,
            "mapping": {
                "start_buttons": ["start", "back"],
                "inputs": {name: {"group": group} for name, group in INPUT_GROUPS.items()},
            },
        }
        meta = recorder.save(os.path.join(self.save_dir, clip), meta)

        pressed_inputs = "+".join(meta["pressed_inputs"])
        with open(self.index_path, "a", newline="") as f:
            csv.writer(f).writerow([clip, meta["duration_s"], meta["n_frames"], pressed_inputs, meta["end_reason"]])
        print(f"Saved {clip}: {meta['duration_s']:.2f} s, {meta['n_frames']} frames, {pressed_inputs} ({meta['end_reason']})")

    def _draw_status(self, frame):
        """Overlays the recorder state and the pressed inputs on the preview."""
        if self.clip_logic.recording:
            button_map = self.joystick_handler.button_map
            pressed = sorted(button_map.display_name(name) for name in self.pressed)
            text = f"REC  saved {self.saved_count}  {' '.join(pressed)}"
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
    parser.add_argument("--subject", default="s00", help="Person / session id, used in the session folder name")
    parser.add_argument("--t_no_input", default=2.0, help="Seconds to wait for an input after Start/Select before stopping")
    parser.add_argument("--t_tail", default=0.5, help="Seconds kept in a clip after the last input is released")
    parser.add_argument("--t_continue", default=1.5, help="Seconds to keep recording after a clip is saved, waiting for a new input")
    parser.add_argument("--t_max", default=10.0, help="Maximum clip duration in seconds")
    parser.add_argument("--fps", default=30.0, help="Camera fps requested for the clips")
    parser.add_argument("--mjpg", action="store_true", help="Request MJPG from the camera (often needed for 60 fps)")

    args = parser.parse_args()

    collector = Collector(args.save_dir, args.subject, float(args.t_no_input), float(args.t_tail), float(args.t_continue), float(args.t_max), float(args.fps), args.mjpg)
    collector.run()
