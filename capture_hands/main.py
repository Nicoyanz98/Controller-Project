import sys, os
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget, QVBoxLayout

from components import NotificationContainer, CaptureInputMenu, MainMenu
from collector import CameraSystem, JoystickManager, JoystickLeftButtonMap, JoystickRightButtonMap, JoystickTriggersButtonMap

class Window(QWidget):
    def __init__(self):
        super().__init__()        
        
        self._create_window()

        self.camera_system = CameraSystem(self, os.path.dirname(os.path.abspath(__file__)))
        self.joystick_manager = JoystickManager(self)

        main_menu_index = self._create_main_menu()

        self.change_menu(main_menu_index)
        self.layout.addWidget(self.page_widget)

    def _create_window(self):
        self.setWindowTitle("Capture Hands")

        self.layout = QVBoxLayout(self)
        self.page_widget = QStackedWidget()

        self.notifications = NotificationContainer(self)
        self.notifications.show()

    def _create_main_menu(self):
        options = []
        for name in self.joystick_manager.get_map_names():
            options.append(CaptureInputMenu(self, name, self.joystick_manager.get_button_sections_for(name)))
        self.main_menu = MainMenu(self, "MAIN", options, False)
        return self.add_page(self.main_menu)
    
    def add_page(self, component):
        page_index = self.page_widget.count()
        component.set_index(page_index)
        self.page_widget.addWidget(component)
        return page_index
    
    def is_camera_connected(self):
        return self.camera_system.is_camera_connected()
    
    def is_joystick_connected(self):
        return self.joystick_manager.is_joystick_connected()
    
    def is_expected_input_pressed(self):
        return self.joystick_manager.is_expected_input_pressed()

    def update_current_input(self, map_name):
        self.joystick_manager.update_expected_input(map_name)

    def get_camera_frame(self):
        return self.camera_system.get_current_frame()
    
    def change_input_expected(self, selected_input):
        self.joystick_manager.listens_for(selected_input)
    
    def save_current_input_frame_as(self, frame_name):
        self.camera_system.save_current_frame(frame_name)

    def notify(self, msg, type, secs):
        self.notifications.add_notification(msg, type, secs)

    def go_back(self):
        self.change_menu(self.main_menu.get_index())

    @Slot(str)
    def change_menu(self, page_index):
        self.page_widget.setCurrentIndex(page_index)

    @Slot(str)
    def notify_error(self, msg):
        self.notify(msg, "error", 2)

    @Slot(str)
    def notify_success(self, msg):
        self.notify(msg, "success", 2)
    
    def notify_warning(self, msg):
        self.notify(msg, "warning", 2)
    
    def closeEvent(self, event):
        self.camera_system.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication([])

    widget = Window()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
        