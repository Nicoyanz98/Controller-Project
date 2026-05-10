from components import Menu, FlowLayout, VideoThread, SideNotification, JoystickThread

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout

class CaptureInputMenu(Menu):
    def _create_menu(self):
        self.thread = {}
        
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

    @Slot(QImage)
    def update_image(self, cv_img):
        qt_img = QPixmap.fromImage(cv_img)
        self.image_label.setPixmap(qt_img)

    def _start_camera_feed(self):
        thread_name = "camera"
        self.thread[thread_name] = VideoThread(self, thread_name)
        self.thread[thread_name].change_pixmap_signal.connect(self.update_image)
        self.thread[thread_name].error_signal.connect(self.notify_error)
        self.thread[thread_name].start()
    
    def _start_joystick_handler(self):
        thread_name = "joystick"
        self.thread[thread_name] = JoystickThread(self, thread_name)
        self.thread[thread_name].error_signal.connect(self.notify_error)
        self.thread[thread_name].success_signal.connect(self.notify_success)
        self.thread[thread_name].start()
    
    @Slot(str)
    def notify_error(self, msg):
        self.notify(msg, "error")

    @Slot(str)
    def notify_success(self, msg):
        self.notify(msg, "success")

    def notify(self, msg, type):
        SideNotification(self.window, msg, type)

    def showEvent(self, event):
        super().showEvent(event)
        self._start_joystick_handler()
        self._start_camera_feed()