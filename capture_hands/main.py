import sys, os
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget, QVBoxLayout

from components import NotificationContainer, CaptureInputMenu, MainMenu
from collector import CameraSystem, JoystickLeftButtonMap, JoystickRightButtonMap, JoystickTriggersButtonMap

class Window(QWidget):
    def __init__(self):
        super().__init__()        
        self._create_window()

        self.camera_system = CameraSystem(self, os.path.dirname(os.path.abspath(__file__)))

    def _create_window(self):
        self.setWindowTitle("Capture Hands")

        self.layout = QVBoxLayout(self)
        self.page_widget = QStackedWidget()
        
        main_menu_index = self._create_main_menu()

        self.change_menu(main_menu_index)
        self.layout.addWidget(self.page_widget)

        self.notifications = NotificationContainer(self)
        self.notifications.show()

    def _create_main_menu(self):
        options = [
            CaptureInputMenu(self, "LEFT", JoystickLeftButtonMap()),
            CaptureInputMenu(self, "RIGHT", JoystickRightButtonMap()),
            CaptureInputMenu(self, "TRIGGERS", JoystickTriggersButtonMap())
        ]
        self.main_menu = MainMenu(self, "MAIN", options, False)
        return self.add_page(self.main_menu)
    
    def add_page(self, component):
        page_index = self.page_widget.count()
        component.set_index(page_index)
        self.page_widget.addWidget(component)
        return page_index
    
    def is_camera_connected(self):
        return self.camera_system.is_camera_connected()

    def get_camera_frame(self):
        return self.camera_system.get_current_frame()

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
        