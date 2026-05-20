import cv2
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage

from components.tasks.thread_task import Thread_Task

class VideoThread(Thread_Task):
    change_pixmap_signal = Signal(QImage)

    def _convert_rgb_image_to_qt_image(self, rgb_image):
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)

    def run(self):
        try:
            while self._run_flag:
                cv2_frame = self.window.get_camera_frame()
                qt_frame = self._convert_rgb_image_to_qt_image(cv2_frame)
                self.change_pixmap_signal.emit(qt_frame)
        except Exception as e:
            self.error_signal.emit(str(e))