from functools import partial

from .menu import Menu
from components import VideoThread, JoystickThread, FlowLayout

from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QButtonGroup

class CaptureInputMenu(Menu):
    def __init__(self, window, name, button_sections, joystick_manager, camera_system, back=True):
        self.joystick_manager = joystick_manager
        self.camera_system = camera_system
        self.button_sections = button_sections
        
        self.button_selector = None
        self.timer = None
        super().__init__(window, name, back)

    def _create_menu(self):
        self.thread_tasks = {}
        
        self._create_header()
        self.layout.addSpacing(60)
        self._create_camera_feed()
        self.layout.addSpacing(20)
        self._create_input_buttons()

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
    
    def _create_input_buttons(self):
        self.button_selector = QButtonGroup()
        self.button_selector.setExclusive(False)
        for input_section in self.button_sections:
            buttons_layout = FlowLayout()
            for joystick_input in input_section:
                button = self._create_button(joystick_input.symbol, buttons_layout, partial(self.toggle_timer_for, joystick_input), toggle=True)
                self.button_selector.addButton(button)
            self.layout.addLayout(buttons_layout)
        
        self.button_selector.buttonToggled.connect(self.change_button_state)

    def change_button_state(self, button, checked):
        for btn in self.button_selector.buttons():
            if btn is not button:
                btn.setEnabled(not checked)

    def toggle_timer_for(self, selected_input, start):
        if start:
            self._notify("warning", f"Started input capture for {selected_input.name}")
            self.timer = QTimer()
            self.timer.timeout.connect(partial(self.capture_input, selected_input))
            
            self._set_expected_input(selected_input)
            self.timer.start(4000)
        else:
            self._notify("warning", f"Stopping input capture for {selected_input.name}")
            self._stop_input_capture()

    def _set_expected_input(self, selected_input):
        self.joystick_manager.listens_for(selected_input)
    
    @Slot(str)
    def _notify(self, type, msg):
        self.window.notify(msg, type)

    def _stop_input_capture(self):
        if self.thread_tasks.get("joystick", False):
            self._set_expected_input(None)

        if self.timer and self.timer.isActive():
            self.timer.stop()
        self.timer = None
    
    def capture_input(self, expected_input):
        if self.joystick_manager.is_expected_input_pressed():
            self.camera_system.save_current_frame(expected_input.name)
        else:
            self.camera_system.save_current_frame("basura")

    def _start_thread_task(self, task, signal_setting=None):
        self.thread_tasks[task.name] = task
        if signal_setting is not None:
            signal_setting(task)
        task.error_signal.connect(partial(self._notify, "error"))
        task.success_signal.connect(partial(self._notify, "success"))
        task.start()

    def go_back(self):
        self._stop_input_capture()
        super().go_back()

    @Slot(str)
    def update_current_input(self, map_name):
        self.joystick_manager.update_expected_input(map_name)

    @Slot(QImage)
    def update_image(self, cv_img):
        qt_img = QPixmap.fromImage(cv_img)
        self.image_label.setPixmap(qt_img)

    def showEvent(self, event):
        super().showEvent(event)
        if self.camera_system.is_camera_connected() and self.joystick_manager.is_joystick_connected():
            self._start_thread_task(VideoThread(self.window, "camera"), lambda task: task.change_pixmap_signal.connect(self.update_image))
            self._start_thread_task(JoystickThread(self.window, "joystick", self.name), lambda task: task.update_input.connect(self.update_current_input))
        else:
            self.go_back()