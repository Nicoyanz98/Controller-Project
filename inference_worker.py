import threading
import time
from typing import List, Optional
 
from slot_assignment import assign_slots
 
class InferenceWorker:
    def __init__(self, cropper, inferencer, n_slots: int = 2):
        self.cropper = cropper
        self.inferencer = inferencer
        self.n_slots = n_slots
 
        self._lock = threading.Lock()
        self._latest_frame = None
        self._frame_seq = 0
        self._processed_seq = -1
 
        self._results: List[Optional[object]] = [None] * n_slots
        self._crop_bounds: List[Optional[tuple]] = [None] * n_slots
        self._prev_centers = [None] * n_slots
 
        self._stop_event = threading.Event()
        self._error: Optional[Exception] = None
        self._thread = threading.Thread(target=self._run, daemon=True, name="InferenceWorker")
 
    def start(self):
        self._thread.start()
        return self
 
    def submit_frame(self, frame):
        """Hand the worker the latest camera frame."""
        with self._lock:
            self._latest_frame = frame.copy()  # defensive: don't share a buffer OpenCV might reuse
            self._frame_seq += 1
 
    def get_results(self):
        """
        Read whatever the worker last finished. Safe to call every frame even if the worker hasn't produced anything
        new since the last call.
        """
        with self._lock:
            return list(self._results), list(self._crop_bounds)
 
    def stop(self, timeout: float = 2.0):
        self._stop_event.set()
        self._thread.join(timeout=timeout)
        if self._error is not None:
            raise self._error
 
    def _run(self):
        try:
            while not self._stop_event.is_set():
                frame, seq = self._take_latest_frame()
                if frame is None or seq == self._processed_seq:
                    time.sleep(0.005)  # nothing ne
                    continue
                self._process_frame(frame, seq)
        except Exception as e:
            # Surface the error to the main thread on stop() rather than letting the worker die 
            # silently and leaving results frozen with no indication anything went wrong.
            self._error = e
            self._stop_event.set()
 
    def _take_latest_frame(self):
        with self._lock:
            return self._latest_frame, self._frame_seq
 
    def _process_frame(self, frame, seq):
        hand_crops = self.cropper.process(frame, source_label=f"live_frame_{seq}")
        assigned, self._prev_centers = assign_slots(self._prev_centers, hand_crops)
 
        new_results = list(self._results)
        new_bounds = list(self._crop_bounds)
        for slot, hc in enumerate(assigned):
            if hc is None:
                continue  # leave that slot's previous result in place
            result = self.inferencer.infer_one(
                hc.crop_rgb, hand_id=f"slot{slot + 1}",
                source_image=hc.source_image, crop_bounds=hc.crop_bounds,
            )
            new_results[slot] = result
            new_bounds[slot] = hc.crop_bounds
 
        with self._lock:
            self._results = new_results
            self._crop_bounds = new_bounds
        self._processed_seq = seq
