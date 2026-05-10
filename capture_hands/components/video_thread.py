import cv2
from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QImage

class VideoThread(QThread):
    change_pixmap_signal = Signal(QImage)
    error_signal = Signal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self._run_flag = True

    def run(self):
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            self.error_signal.emit("No camera connected")
            return
        
        try:
            while self._run_flag:
                ret, frame = cap.read()
                if ret:
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
                    self.change_pixmap_signal.emit(p)
                else:
                    self.error_signal.emit("Lost camera connection")
                    break
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()