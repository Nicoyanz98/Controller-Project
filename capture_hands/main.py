import sys
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget, QVBoxLayout

from components import SideNotification
from pages import CaptureInputMenu, MainMenu

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Capture Hands")
        
        self.layout = QVBoxLayout(self)
        self.page_widget = QStackedWidget()

        self.main_menu = MainMenu(self, "MAIN", [(CaptureInputMenu, "LEFT"), (CaptureInputMenu, "RIGHT")])

        self.layout.addWidget(self.page_widget)
    
    def add_page(self, component):
        page_index = self.page_widget.count()
        component.set_index(page_index)
        self.page_widget.addWidget(component)
        return page_index

    @Slot(str)
    def change_menu(self, page_index):
        self.page_widget.setCurrentIndex(page_index)

if __name__ == "__main__":
    app = QApplication([])

    widget = Window()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
        