from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
from functools import partial

from components import Menu, FlowLayout

class MainMenu(Menu):
    def __init__(self, window, name, options=[]):
        self.options = options
        super().__init__(window, name)

    def _create_menu(self):
        self.window.add_page(self)

        self._create_header()
        self.layout.addSpacing(60)
        self._create_options_buttons()

    def _create_options_buttons(self):
        buttons_layout = FlowLayout()

        for component, name in self.options:
            option_index = self.window.add_page(component(self.window, name, self.index))
            self._create_button(name, buttons_layout, partial(self.window.change_menu, option_index))

        self.layout.addLayout(buttons_layout)

    def _create_header(self):
        self.setStyleSheet("""
            QLabel#title {
                font-size: 28px;
                font-weight: bold;
            }

            QLabel#subtitle {
                font-size: 16px;
                color: gray;
            }
        """)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(0)

        title = QLabel("Main Menu")
        title.setAlignment(Qt.AlignHCenter)
        title.setObjectName("title")

        subtitle = QLabel("Choose an input mode")
        subtitle.setAlignment(Qt.AlignHCenter)
        subtitle.setObjectName("subtitle")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        self.layout.addLayout(header_layout)