from menu import Menu
from components import VideoThread, JoystickThread

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout

class CaptureInputMenu(Menu):
    def _create_menu(self):
        self.thread_tasks = {}
        
        self._create_header()
        self.layout.addSpacing(60)
        self._create_camera_feed()
        self.layout.addSpacing(20)

    def _create_camera_feed(self):
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignHCenter)
        self.image_label.resize(640, 480)
        self.layout.addWidget(self.image_label)

    def _create_header(self):
        self.setStyleSheet("""
            QLabel#title {
                font-size: 28px;
                font-weight: bold;
            }
        """)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(0)

        title = QLabel("Capturar botones")
        title.setAlignment(Qt.AlignHCenter)
        title.setObjectName("title")

        header_layout.addWidget(title)

        self.layout.addLayout(header_layout)

    def _start_thread_task(self, task, name):
        self.thread_tasks[name] = task(self, name)
        task.change_pixmap_signal.connect(self.update_image)
        task.error_signal.connect(self.notify_error)
        task.start()

    @Slot(QImage)
    def update_image(self, cv_img):
        qt_img = QPixmap.fromImage(cv_img)
        self.image_label.setPixmap(qt_img)
    
    @Slot(str)
    def notify_error(self, msg):
        self.window.notify(msg, "error")

    @Slot(str)
    def notify_success(self, msg):
        self.window.notify(msg, "success")

    def showEvent(self, event):
        super().showEvent(event)
        self._start_thread_task(VideoThread, "camera")
        self._start_thread_task(JoystickThread, "joystick")