import sys, os
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget, QVBoxLayout
from functools import partial

from components import NotificationContainer, CaptureInputMenu, MainMenu
from collector import CameraSystem, JoystickManager

class Window(QWidget):
    def __init__(self):
        super().__init__()        
        
        self._create_window()

        self.joystick_manager = JoystickManager(self, "Joystick Manager")
        self.camera_system = CameraSystem(self, "Camera System", os.path.dirname(os.path.abspath(__file__)))

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
            button_sections = self.joystick_manager.get_button_sections_for(name)
            options.append(CaptureInputMenu(self, name, button_sections, self.joystick_manager, self.camera_system))
        self.main_menu = MainMenu(self, "MAIN", options, False)
        return self.add_page(self.main_menu)
    
    def add_page(self, component):
        page_index = self.page_widget.count()
        component.set_index(page_index)
        self.page_widget.addWidget(component)
        return page_index
    
    def notify(self, msg, type, secs=2):
        self.notifications.add_notification(msg, type, secs)

    def go_back(self):
        if hasattr("main_menu", self):
            self.main_menu.reset_capture()
            self.change_menu(self.main_menu.get_index())

    @Slot(str)
    def change_menu(self, page_index):
        self.page_widget.setCurrentIndex(page_index)
    
    def closeEvent(self, event):
        self.camera_system.close()
        self.joystick_manager.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication([])

    widget = Window()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
        