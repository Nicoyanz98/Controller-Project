from functools import partial

from .menu import Menu
from components import FlowLayout

from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QButtonGroup, QSizePolicy

class CaptureInputMenu(Menu):
    def __init__(self, window, name, button_sections, joystick_manager, camera_system, back=True):
        self.joystick_manager = joystick_manager
        self.camera_system = camera_system
        self.button_sections = button_sections
        
        self.button_selector = None
        self.capture_timer = None
        self.feedback_timer = None
        super().__init__(window, name, back)

    def _create_menu(self):
        self._create_header()
        self.layout.addSpacing(60)
        self._create_camera_feed()
        self.layout.addSpacing(20)
        self._create_input_buttons()

    def _create_camera_feed(self):
        self.image_label = QLabel(self)
        self.image_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.image_label.setAlignment(Qt.AlignHCenter)
        self.current_pixmap = None
        # self.image_label.resize(640, 480)
        self.layout.addWidget(self.image_label)

    def receive_frame(self, cv_img):
        self.current_pixmap = QPixmap.fromImage(cv_img)
        self._update_camera_display()

    def _update_camera_display(self):
        if not self.current_pixmap:
            return

        scaled = self.current_pixmap.scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.image_label.setPixmap(scaled)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_camera_display()

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

    @Slot(object, bool)
    def toggle_timer_for(self, selected_input, start):
        if start:
            self._notify("warning", f"Started input capture for {selected_input.name}")
            self.capture_timer = QTimer()
            self.capture_timer.timeout.connect(partial(self.capture_input, selected_input))
            
            self.feedback_timer = QTimer()
            self.feedback_timer.timeout.connect(self.update_input_feedback)
            
            self._set_expected_input(selected_input)
            self.capture_timer.start(4000)
            self.feedback_timer.start(50)
        else:
            self._notify("warning", f"Stopping input capture for {selected_input.name}")
            self.stop_input_capture()

    def _set_expected_input(self, selected_input):
        self.joystick_manager.listens_for(selected_input)
    
    def _notify(self, type, msg):
        self.window.notify(msg, type)

    def stop_input_capture(self):
        self._set_expected_input(None)

        if self.capture_timer is not None and self.capture_timer.isActive():
            self.capture_timer.stop()

        if self.feedback_timer is not None and self.feedback_timer.isActive():
            self.feedback_timer.stop()
        
        self.feedback_timer = None

        self.capture_timer = None
        self.image_label.setStyleSheet("")
    
    @Slot()
    def update_input_feedback(self):
        pressed = self.joystick_manager.is_expected_input_pressed()
        if pressed:
            self.image_label.setStyleSheet("""
                QLabel {
                    border: 4px solid green;
                }
            """)
        else:
            self.image_label.setStyleSheet("""
                QLabel {
                    border: 4px solid yellow;
                }
            """)

    @Slot(object)
    def capture_input(self, expected_input):
        if self.joystick_manager.is_expected_input_pressed():
            self.camera_system.save_current_frame(expected_input.name)
        else:
            self.camera_system.save_current_frame("basura")

    def go_back(self):
        self.stop_input_capture()
        self.camera_system.unsubscribe(self)
        super().go_back()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.camera_system.is_camera_connected() or not self.joystick_manager.is_joystick_connected():
            self.go_back()
        
        self.camera_system.subscribe(self)