from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout
from functools import partial

from .menu import Menu
from components import FlowLayout

class MainMenu(Menu):
    def _create_menu(self):
        self._create_header()
        self.layout.addSpacing(60)
        # self._create_options_buttons()

    def create_options_buttons(self, options):
        buttons_layout = FlowLayout()

        for component in options:
            option_index = self.window.add_page(component)
            component.set_back_index(self.index)
            self._create_button(component.get_name(), buttons_layout, partial(self.window.change_menu, option_index))

        self.layout.insertLayout(4, buttons_layout)

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