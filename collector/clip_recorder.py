import os
import csv
import json
import queue
import threading
from bisect import bisect_right

import cv2

from controller_button_map import INPUT_GROUPS, LABEL_GROUPS, AXIS_NAMES, group_labels


class ClipLogic:
    """Decides when clips start and end from the joystick state.

    update() returns:
        "start"   -> Start/Select pressed while idle, the first clip begins at t0
        "save"    -> the clip ended after its inputs were released, keep it
        "discard" -> the clip ended without any input, throw it away
        None      -> nothing changed

    After a clip ends the recorder keeps going: a new clip begins at the previous
    "stop_t" and waits "continue_time" seconds for a new input before stopping.
    Pressing Start/Select while recording ends the current clip and stops the recorder.
    "recording" tells whether a new clip follows a "save"/"discard".
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
        # Controller state, stored only when it changes
        self.sample_times = []
        self.samples = []
        self.poll_count = 0
        self.first_poll_t = None
        self.last_poll_t = None

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

    def add_sample(self, t, pressed, axes):
        """Registers the controller state (pressed inputs and axis values) at time t."""
        self.poll_count += 1
        if self.first_poll_t is None:
            self.first_poll_t = t
        self.last_poll_t = t

        if self.samples and self.samples[-1] == (pressed, axes):
            return
        self.sample_times.append(t)
        self.samples.append((pressed, axes))

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

    def save(self, stem, meta):
        """Moves the video to <stem>.mp4 and writes next to it, with times since t0, 
        and returns the completed meta:
            - "stem"_frames.csv: per frame: group labels, 0/1 per input and axis values
            - "stem"_events.csv: press/release of every input
            - "stem".json: meta plus clip stats
        """
        os.replace(self.path, f"{stem}.mp4")
        self.path = f"{stem}.mp4"

        names = list(INPUT_GROUPS)
        with open(f"{stem}_frames.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["frame", "t"] + LABEL_GROUPS + names + [f"axis_{name}" for name in AXIS_NAMES])
            for frame_idx, frame_t in enumerate(self.frame_times):
                pressed, axes = self._sample_at(frame_t)
                labels = group_labels(pressed)
                row = [frame_idx, f"{frame_t - self.t0:.4f}"]
                row += [labels[group] for group in LABEL_GROUPS]
                row += [int(name in pressed) for name in names]
                row += [f"{value:.4f}" for value in axes]
                writer.writerow(row)

        events = self._events()
        with open(f"{stem}_events.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["t", "input", "event"])
            for t, name, event in events:
                writer.writerow([f"{t:.4f}", name, event])

        meta.update(self._stats(meta["fps_measured"], events))
        with open(f"{stem}.json", "w") as f:
            json.dump(meta, f, indent=2)
        return meta

    def _sample_at(self, t):
        """Last controller state registered at or before t (the first one for earlier frames)."""
        idx = max(bisect_right(self.sample_times, t) - 1, 0)
        return self.samples[idx]

    def _events(self):
        """(t since t0, input, "press"/"release") for every change of the pressed inputs."""
        events = []
        previous = frozenset()
        for t, (pressed, _) in zip(self.sample_times, self.samples):
            for name in INPUT_GROUPS:
                if name in pressed and name not in previous:
                    events.append((t - self.t0, name, "press"))
                elif name in previous and name not in pressed:
                    events.append((t - self.t0, name, "release"))
            previous = pressed
        return events

    def _stats(self, fps, events):
        """Clip duration, frame gaps and pressed inputs, saved in the clip json."""
        frame_times = self.frame_times
        gaps = [b - a for a, b in zip(frame_times, frame_times[1:])]
        nominal_gap = 1.0 / fps
        poll_time = self.last_poll_t - self.first_poll_t if self.poll_count > 1 else 0
        return {
            "n_frames": len(frame_times),
            "duration_s": round(frame_times[-1] - self.t0, 4),
            "first_frame_t": round(frame_times[0] - self.t0, 4),
            "max_frame_gap_s": round(max(gaps), 4) if gaps else None,
            "frame_gaps_over_1.5x": sum(gap > 1.5 * nominal_gap for gap in gaps),
            "poll_rate_hz": round(self.poll_count / poll_time, 1) if poll_time > 0 else None,
            "n_press_events": sum(event == "press" for _, _, event in events),
            "pressed_inputs": sorted({name for _, name, event in events if event == "press"}),
            "label_groups": LABEL_GROUPS,
        }

    def delete(self):
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass
