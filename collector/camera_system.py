import cv2
import threading
import os
from time import time

class CameraSystem:
    def __init__(self):
        self.camera_thread = threading.Thread(target=self._camera_worker, daemon=True)
        self.running = False

        self.frame = None
        self.frame_lock = threading.Lock()

    def _camera_worker(self):
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    break

                with self.frame_lock:
                    self.frame = frame.copy()
        finally:
            self.cap.release()
            cv2.destroyAllWindows()        

    def get_frame(self):
        with self.frame_lock:
            if self.frame is not None:
                return self.frame.copy()
            else:
                return None

    def start(self):
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.camera_thread.start()

        while True:
            if (frame := self.get_frame()) is not None:
                cv2.imshow("Camera Feed", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def stop(self):
        self.running = False
        self.camera_thread.join()

    def save_frame(self, filename):
        frame = self.get_frame()
        filename = os.path.join(f"{filename}_{time().strftime('%Y%m%d_%H%M%S')}.jpg")
        if frame is not None:
            cv2.imwrite(filename, frame)
            print(f"Saved frame to {filename}")
        else:
            print("No frame available to save.")