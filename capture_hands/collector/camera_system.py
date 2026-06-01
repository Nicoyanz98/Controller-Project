import cv2, os, time
from collector import VideoThread
from functools import partial
from PySide6.QtGui import QImage
from PySide6.QtCore import Slot

class CameraSystem():
    def __init__(self, window, dir_path):
        self.data_dir = os.path.join(dir_path, "data")
        self.window = window
        self.subscribers = []

        self.thread = VideoThread(self, "Camera")
        self.thread.error_signal.connect(partial(self._notify, "error"))
        self.thread.error_signal.connect(self.window.go_back)
        self.thread.success_signal.connect(partial(self._notify, "success"))
        self.thread.change_pixmap_signal.connect(self.notify_current_frame)

        self.thread.start()

    def close(self):
        self.camera_connected = False
    
    def is_camera_connected(self):
        is_connected = self.thread.is_camera_connected()
        if not is_connected:
            self._notify("error", "No camera connected")
        return is_connected

    def subscribe(self, sub):
        self.subscribers.append(sub)
    
    def unsubscribe(self, sub):
        self.subscribers =  [s for s in self.subscribers if s is not sub]

    def notify_subscriber(self, frame):
        for sub in self.subscribers:
            sub.receive_frame(frame)

    @Slot(QImage)
    def notify_current_frame(self, curr_frame):
        self.notify_subscribers(curr_frame)
        
    def save_current_frame(self, frame_name):
        capture_dir = os.path.join(self.data_dir, frame_name)
        try:
            frame_rgb = self.thread.get_current_frame()
            if frame_rgb is not None:
                raise Exception("Current frame not available")
            
            os.makedirs(capture_dir, exist_ok=True)
            pic_count = len([pic for pic in os.listdir(capture_dir) if pic.endswith('.jpg')])

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{pic_count}_{frame_name}_{timestamp}.jpg"
            filepath = os.path.join(capture_dir, filename)
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            saved = cv2.imwrite(filepath, frame_bgr)
            
            if saved:
                capture_msg = f"Frame saved at: {os.path.join(os.path.basename(capture_dir), filename)}"
                if "trash" == frame_name:
                    self.window.notify(capture_msg, "warning")
                else:
                    self.window.notify(capture_msg, "success")
            else:
                self.window.notify(f"Failure during saving: cv2.imwrite()", "error")
        except Exception as e:
            print(e)
            self.window.notify(f"Failure during saving: {e}", "error")
    
    def close(self):
        self.thread.stop()
        self.set_current_button_map(None)