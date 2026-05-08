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
        self.pages = QStackedWidget()

        pages = [MainMenu(self, "MAIN"), CaptureInputMenu(self, "LEFT"), CaptureInputMenu(self, "RIGHT")]
        for page in pages:
            self.pages.addWidget(page)

        self.layout.addWidget(self.pages)
    
    @Slot(str)
    def change_menu(self, page_index):
        self.pages.setCurrentIndex(page_index)

if __name__ == "__main__":
    app = QApplication([])

    widget = Window()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
        