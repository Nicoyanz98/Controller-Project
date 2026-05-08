from abc import abstractmethod
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

class Menu(QWidget):
    def __init__(self, window, name):
        super().__init__()

        self.window = window
        self.name = name

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignTop)

        self.layout.addStretch()

        self._create_menu()

        self.layout.addStretch()

    @abstractmethod
    def _create_menu(self):
        pass

    @abstractmethod
    def _create_header(self):
        pass
    
    def _create_button(self, text, layout, func):
        button = QPushButton(text)
        button.clicked.connect(func)
        button.setMinimumSize(140, 60)
        layout.addWidget(button)