import cv2
import threading
import os
from time import time, sleep, strftime

class CameraSystem:
    def __init__(self):
        self.camera_thread = threading.Thread(target=self._camera_worker, daemon=True)
        self.running = False

        self._init_camera()

        self.frame = None
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
        self.running = True
        self.camera_thread.start()

    def stop(self):
        self.running = False
        self.camera_thread.join()

    def save_frame(self, filename):
        frame = self.get_frame()
        filename = os.path.join(f"{filename}_{strftime('%Y%m%d-%H%M%S')}.jpg")
        if frame is not None:
            if cv2.imwrite(filename, frame):
                print(f"Saved frame to {filename}")
            else:
                print("Saving error")                
        else:
            print("No frame available to save.")