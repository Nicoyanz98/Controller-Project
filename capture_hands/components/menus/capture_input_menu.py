from functools import partial

from .menu import Menu
from components import VideoThread, JoystickThread, FlowLayout

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout

class CaptureInputMenu(Menu):
    def __init__(self, window, name, button_map, back=True):
        self.button_map = button_map
        self.initialized_buttons = False
        super().__init__(window, name, back)

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
    
    @Slot()
    def create_buttons(self):
        if not self.initialized_buttons:
            layoutIndex = 5
            input_sections = [self.button_map.get_buttons(), self.button_map.get_sticks(), self.button_map.get_dpads()]
            for i, input_section in enumerate(input_sections):
                buttons_layout = FlowLayout()
                for btn_text, btn_name, value in input_section:
                    self._create_button(btn_text, buttons_layout, partial(print, btn_name))
                self.layout.insertLayout(layoutIndex + i, buttons_layout)
            
            self.initialized_buttons = True

    def _start_thread_task(self, task, signal_setting):
        self.thread_tasks[task.name] = task
        signal_setting(task)
        task.error_signal.connect(self.notify_error)
        task.success_signal.connect(self.notify_success)
        task.start()

    @Slot(QImage)
    def update_image(self, cv_img):
        qt_img = QPixmap.fromImage(cv_img)
        self.image_label.setPixmap(qt_img)
    
    @Slot(str)
    def notify_error(self, msg):
        self.window.notify(msg, "error", 2)

    @Slot(str)
    def notify_success(self, msg):
        self.window.notify(msg, "success", 2)

    def showEvent(self, event):
        super().showEvent(event)
        self._start_thread_task(VideoThread(self, "camera"), lambda task: task.change_pixmap_signal.connect(self.update_image))
        self._start_thread_task(JoystickThread(self, "joystick", self.button_map), lambda task: task.buttons_intialized.connect(self.create_buttons))