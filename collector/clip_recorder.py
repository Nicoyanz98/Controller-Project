import os
import csv
import queue
import threading
from bisect import bisect_right

import cv2


class ClipLogic:
    """Decides when clips start and end from the joystick state.

    update() returns:
        "start"   -> Start/Select pressed while idle, the first clip begins at t0
        "save"    -> the clip ended after its inputs were released, keep it
        "discard" -> the clip ended without any input, throw it away
        None      -> nothing changed

    After a clip ends the recorder keeps going: a new clip begins at the previous
    stop_t and waits continue_time seconds for a new input before stopping.
    Pressing Start/Select while recording ends the current clip and stops the recorder.
    .recording tells whether a new clip follows a "save"/"discard".
    """

    def __init__(self, no_press_timeout=2.0, tail=0.5, continue_time=1.5, max_duration=10.0):
        self.no_press_timeout = no_press_timeout
        self.tail = tail
        self.continue_time = continue_time
        self.max_duration = max_duration

        self.recording = False
        self.t0 = None
        self.stop_t = None
        self.reason = ""

        self._press_timeout = no_press_timeout
        self._had_press = False
        self._release_t = None

    def update(self, t, toggle_pressed, any_pressed):
        if not self.recording:
            # Start recording
            if toggle_pressed:
                self.recording = True
                self.stop_t = None
                self.reason = ""
                self._begin_clip(t, self.no_press_timeout)
                return "start"
            return None

        # Stop recording on a second Start/Select press
        if toggle_pressed:
            self.recording = False
            action = "save" if self._had_press else "discard"
            return self._end_clip(t, action, "stopped by user")

        # Mark a press
        if any_pressed:
            self._had_press = True
            self._release_t = None
        # Mark start of release
        elif self._had_press and self._release_t is None:
            self._release_t = t

        # Stop recording after no input
        if not self._had_press and t - self.t0 >= self._press_timeout:
            self.recording = False
            return self._end_clip(t, "discard", "no input within timeout")
        # End clip after release
        if self._release_t is not None and t - self._release_t >= self.tail:
            return self._end_clip(self._release_t + self.tail, "save", "released")
        # End clip for max duration
        if t - self.t0 >= self.max_duration:
            return self._end_clip(t, "save", "max duration reached")
        return None

    def _begin_clip(self, t0, press_timeout):
        """Resets the clip state, the clip is discarded if no input arrives within press_timeout."""
        self.t0 = t0
        self._press_timeout = press_timeout
        self._had_press = False
        self._release_t = None

    def _end_clip(self, stop_t, action, reason):
        """Closes the current clip and, if still recording, chains the next one right after it."""
        self.stop_t = stop_t
        self.reason = reason
        if self.recording:
            self._begin_clip(stop_t, self.continue_time)
        return action


class ClipRecorder:
    """Writes the frames of one clip on its own thread so the camera never waits on encoding."""

    def __init__(self, path, fps, size, t0, fourcc="mp4v"):
        self.path = path
        self.t0 = t0
        self.stop_t = None

        self.frame_times = []
        self.label_times = []
        self.labels = []

        self.frame_queue = queue.Queue(maxsize=600)
        self.writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*fourcc), fps, size)
        if not self.writer.isOpened():
            raise RuntimeError(f"Could not open video writer for {path} (fourcc={fourcc})")

        self.writer_thread = threading.Thread(target=self._writer_worker, daemon=True)
        self.writer_thread.start()

    def push(self, frame, t):
        """Camera sink: queues the frames captured after the clip start."""
        if t < self.t0:
            return
        try:
            self.frame_queue.put_nowait((frame, t))
        except queue.Full:
            pass # Dropped frames show up as gaps in frame_times

    def add_label(self, t, label):
        """Registers the joystick label active from time t (only stored when it changes)."""
        if self.labels and self.labels[-1] == label:
            return
        self.label_times.append(t)
        self.labels.append(label)

    def _writer_worker(self):
        while True:
            item = self.frame_queue.get()
            if item is None:
                break

            frame, t = item
            if self.stop_t is not None and t > self.stop_t:
                continue
            self.writer.write(frame)
            self.frame_times.append(t)

    def close(self, stop_t):
        """Stops the writer, frames after stop_t are left out of the clip."""
        self.stop_t = stop_t
        self.frame_queue.put(None)
        self.writer_thread.join()
        self.writer.release()

    def save(self, path):
        """Moves the video to path and writes its per-frame labels next to it."""
        os.replace(self.path, path)
        self.path = path

        labels_path = os.path.splitext(path)[0] + "_labels.csv"
        with open(labels_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["frame", "t", "label"])
            for frame_idx, frame_t in enumerate(self.frame_times):
                writer.writerow([frame_idx, f"{frame_t - self.t0:.4f}", self._label_at(frame_t)])

    def _label_at(self, t):
        """Last label registered at or before t (the first one for earlier frames)."""
        idx = max(bisect_right(self.label_times, t) - 1, 0)
        return self.labels[idx]

    def delete(self):
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass
