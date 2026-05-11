from abc import abstractmethod
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from components import FlowLayout

class Menu(QWidget):
    def __init__(self, window, name, parent_index=None):
        super().__init__()

        self.window = window
        self.name = name
        self.parent_index = parent_index

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignTop)

        self.layout.addStretch()
        self._create_menu()
        self.layout.addSpacing(40)
        self._create_extra_button()
        self.layout.addStretch()

    @abstractmethod
    def _create_menu(self):
        pass

    @abstractmethod
    def _create_header(self):
        pass

    def _create_extra_button(self):
        extra_button_layout = FlowLayout()
        if self.parent_index is not None:
            self._create_button("BACK", extra_button_layout, self.go_back)
        else:
            self._create_button("QUIT", extra_button_layout, self.window.close)
        self.layout.addLayout(extra_button_layout)

    def set_index(self, index):
        self.index = index
    
    def _create_button(self, text, layout, func):
        button = QPushButton(text)
        button.clicked.connect(func)
        button.setMinimumSize(140, 60)
        layout.addWidget(button)
    
    def go_back(self):
        if self.thread_tasks:
            for task in self.thread_tasks.values():
                task.stop()
        self.image_label.clear()
        self.window.change_menu(self.parent_index)
    
    def _create_back_button(self, layout):
        self._create_button("BACK", layout, self.go_back)
        self.layout.addLayout(layout)

    