import cv2
from PySide6.QtCore import Qt, Signal, QMutex, QMutexLocker
from PySide6.QtGui import QImage

from collector.tasks import Thread_Task

class VideoThread(Thread_Task):
    change_pixmap_signal = Signal(QImage)

    def __init__(self, manager, name):
        super().__init__(manager, name)

        self.cap = cv2.VideoCapture(0)

        self.camera_connected = False
        self.connection_lock = QMutex()
        with QMutexLocker(self.connection_lock):
            self.camera_connected = self.cap.isOpened()
            if self.camera_connected:
                self.success_signal.emit("Camera connected")
    
    def is_camera_connected(self):
        with QMutexLocker(self.connection_lock):
            connected = self.camera_connected
        return connected

    def get_current_frame(self):
        ret, frame = self.cap.read()
        with QMutexLocker(self.connection_lock):
            self.camera_connected = ret
        
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            self.error_signal.emit("Camera disconnected")
            return None

    def _convert_rgb_image_to_qt_image(self, rgb_image):
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)

    def _update_camera_frame(self):
        cv2_frame = self.get_current_frame()
        if cv2_frame is not None:
            qt_frame = self._convert_rgb_image_to_qt_image(cv2_frame)
            self.change_pixmap_signal.emit(qt_frame)

    def run(self):
        try:
            while self._run_flag:
                self._update_camera_frame()
            
                self.msleep(2)
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.cap.release()
    
    def stop(self):
        super().stop()