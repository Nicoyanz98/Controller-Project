from functools import partial

from .menu import Menu
from components import VideoThread, JoystickThread, FlowLayout

from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QButtonGroup

class CaptureInputMenu(Menu):
    def __init__(self, window, name, button_map, back=True):
        self.button_map = button_map
        self.button_selector = None
        self.current_frame = None
        self.timer = None
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
    def create_input_buttons(self):
        if not self.initialized_buttons:
            layoutIndex = 5
            self.button_selector = QButtonGroup()
            self.button_selector.setExclusive(False)
            input_sections = [self.button_map.get_buttons(), self.button_map.get_sticks(), self.button_map.get_dpads()]
            for i, input_section in enumerate(input_sections):
                buttons_layout = FlowLayout()
                for joystick_input in input_section:
                    button = self._create_button(joystick_input.symbol, buttons_layout, partial(self.toggle_timer_for, joystick_input), toggle=True)
                    self.button_selector.addButton(button)
                self.layout.insertLayout(layoutIndex + i, buttons_layout)
            
            self.button_selector.buttonToggled.connect(self.change_button_state)
            self.initialized_buttons = True

    def change_button_state(self, button, checked):
        for btn in self.button_selector.buttons():
            if btn is not button:
                btn.setEnabled(not checked)

    def toggle_timer_for(self, selected_input, start):
        if start:
            self.window.notify_warning(f"Started input capture for {selected_input.name}")
            self.timer = QTimer()
            self.timer.timeout.connect(partial(self.capture_input, selected_input))
            
            self.thread_tasks["joystick"].listen_for(selected_input)
            self.timer.start(4000)
        else:
            self.window.notify_warning(f"Stopping input capture for {selected_input.name}")
            self._stop_input_capture()

    def _stop_input_capture(self):
        if self.thread_tasks.get("joystick", False):
            self.thread_tasks["joystick"].listen_for(None)
            
        if self.timer and self.timer.isActive():
            self.timer.stop()
        self.timer = None
    
    def capture_input(self, expected_input):
        #  try:
        #     # Verificamos que el directorio existe (por si acaso)
        #     os.makedirs(self.capture_dir, exist_ok=True)
        
        #     # Contamos los archivos JPG en el directorio
        #     pic_count = len([pic for pic in os.listdir(self.capture_dir) if pic.endswith('.jpg')])

        #     timestamp = time.strftime("%Y%m%d_%H%M%S")
        #     filename = f"{self.capture_dir}/{pic_count}_{self.capture_dir}_{timestamp}.jpg"
        #     frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        #     cv2.imwrite(filename, frame_bgr)

        #     if "basura" in self.capture_dir:
        #         self.last_capture_status = "trash"
        #         print(f"Captura enviada a BASURA: {filename}")
        #     else:
        #         self.last_capture_status = "success"
        #         print(f"Captura guardada correctamente: {filename}")

        #     self.last_capture_time = time.time()
            
        # except Exception as e:
        #     print(f"Error en captura automática: {e}")

        # Saving logic
        if self.thread_tasks["joystick"].is_expected_input_pressed():
            # Preserve button name
            print(f"Input {expected_input.name} pressed")
        else:
            # Considered as "nothing"
            print("Expected input not pressed")

    def _start_thread_task(self, task, signal_setting):
        self.thread_tasks[task.name] = task
        signal_setting(task)
        task.error_signal.connect(self.window.notify_error)
        task.success_signal.connect(self.window.notify_success)
        task.start()

    def go_back(self):
        self._stop_input_capture()
        self.current_frame = None
        super().go_back()

    @Slot(QImage)
    def update_image(self, cv_img):
        self.current_frame = cv_img
        qt_img = QPixmap.fromImage(cv_img)
        self.image_label.setPixmap(qt_img)

    def showEvent(self, event):
        super().showEvent(event)
        if self.window.is_camera_connected():
            self._start_thread_task(VideoThread(self.window, "camera"), lambda task: task.change_pixmap_signal.connect(self.update_image))
            self._start_thread_task(JoystickThread(self.window, "joystick", self.button_map), lambda task: task.buttons_intialized.connect(self.create_input_buttons))
        else:
            self.go_back()