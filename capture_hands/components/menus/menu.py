from abc import abstractmethod
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from components import FlowLayout

class Menu(QWidget):
    def __init__(self, window, name, back):
        super().__init__()

        self.window = window
        self.name = name
        self.back = back

        self.set_index(None)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignTop)

        self.layout.addStretch()
        self._create_menu()
        self.layout.addSpacing(20)
        self._create_extra_button()
        self.layout.addStretch()

    def get_name(self):
        return self.name
    
    def set_back_index(self, back_index):
        self.back_index = back_index
    
    def set_index(self, index):
        self.index = index
    
    def get_index(self):
        return self.index

    @abstractmethod
    def _create_menu(self):
        pass

    @abstractmethod
    def _create_header(self):
        pass

    def _create_extra_button(self):
        extra_button_layout = FlowLayout()
        if self.back:
            self._create_button("BACK", extra_button_layout, self.go_back)
        else:
            self._create_button("QUIT", extra_button_layout, self.window.close)
        self.layout.addLayout(extra_button_layout)
    
    def _create_button(self, text, layout, func=None, toggle=False):
        button = QPushButton(text)
        button.setMinimumSize(100, 60)
        button.setStyleSheet("font-size: 20px")
        
        if toggle:
            button.setCheckable(True)
        
        if func is not None:
            if toggle:
                button.toggled.connect(func)
            else:
                button.clicked.connect(func)

        layout.addWidget(button)
        return button
    
    def go_back(self):
        self.image_label.clear()
        self.window.go_back()
    
    def _create_back_button(self, layout):
        self._create_button("BACK", layout, self.go_back)
        self.layout.addLayout(layout)

    