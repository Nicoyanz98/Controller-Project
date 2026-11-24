from ultralytics import YOLO
import threading
from time import sleep
import numpy as np

class AsyncYOLO:
    def __init__(self, model_path, callback_fn=None):
        self.model = YOLO(model_path)

        self.next_frame = None
        self.frame_ready_event = threading.Event()
        self.lock = threading.Lock()

        self.callback = callback_fn

        self.options = {
            "persist": True, 
            "verbose": False, 
            "tracker": "./bytetracker.yaml", 
            "iou": 0.7, 
            "conf": 0.4
        }

    def track(self, frame):
        results = self.model.track(frame, **self.options)
        
        if self.callback is not None and results:
            self.callback(results[0])

    def track_async(self, frame):
        with self.lock:
            self.next_frame = frame.copy() if frame is not None else None
        self.frame_ready_event.set()

    def start(self):
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        self._warmup()

    def _warmup(self):
        dummy_frame = 255 * np.ones((224, 224, 3), dtype=np.uint8)
        self.model.track(dummy_frame)

    def _worker(self):
        while self.running:
            self.frame_ready_event.wait()
            self.frame_ready_event.clear()

            with self.lock:
                frame_to_process = self.next_frame
                self.next_frame = None

            if frame_to_process is not None:
                results = self.model.track(frame_to_process, **self.options)
                
                if self.callback is not None and results:
                    self.callback(results[0])
            # sleep(0.01)