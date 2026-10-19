import cv2
import threading
from time import perf_counter, sleep

class CameraSystem:
    """Reads camera frames on its own thread, timestamps them and forwards them to an optional sink."""

    def __init__(self, fps=30, mjpg=False):
        self.fps = fps
        self.mjpg = mjpg

        self.camera_thread = threading.Thread(target=self._camera_worker, daemon=True)
        self.running = False

        self._init_camera()

        self.frame = None
        self.frame_count = 0
        self.sink = None
        self.frame_lock = threading.Lock()

    def _init_camera(self):
        warned = False
        while True:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                break

            if not warned:
                print("Please connect a camera")
                warned = True

            if self.cap:
                self.cap.release()
            sleep(1)
        print("Camera detected")
        # MJPG is often needed for the camera to deliver high fps
        if self.mjpg:
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

    def _camera_worker(self):
        try:
            while self.running:
                ret, frame = self.cap.read()
                t = perf_counter()
                if not ret:
                    print("here")
                    break

                with self.frame_lock:
                    self.frame = frame
                    self.frame_count += 1
                    sink = self.sink

                # Sends the frame to the clip being recorded
                if sink is not None:
                    sink(frame, t)
        finally:
            self.cap.release()

    def get_frame(self):
        with self.frame_lock:
            if self.frame is not None:
                return self.frame.copy()
            else:
                return None

    def set_sink(self, sink):
        """sink(frame, t) is called for every new frame, None disables it."""
        with self.frame_lock:
            self.sink = sink

    def measure_fps(self, seconds=1.5):
        """Measures the real camera fps and frame size, used to write the clips."""
        sleep(0.5) # warm-up
        with self.frame_lock:
            start_count = self.frame_count
        sleep(seconds)
        with self.frame_lock:
            end_count = self.frame_count
            frame = self.frame

        if frame is None:
            raise RuntimeError("Camera opened but returns no frames")
        fps = (end_count - start_count) / seconds
        size = (frame.shape[1], frame.shape[0])
        return fps, size

    def start(self):
        self.running = True
        self.camera_thread.start()

    def stop(self):
        self.running = False
        self.camera_thread.join()
