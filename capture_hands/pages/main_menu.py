from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
from functools import partial

from components import Menu, FlowLayout

class MainMenu(Menu):
    def _create_menu(self):
        self._create_header()
        self.layout.addSpacing(60)
        self._create_options_buttons()

    def _create_options_buttons(self):
        buttons_layout = FlowLayout()
        options = ["LEFT", "RIGHT", "TRIGGERS"]
        for o in options:
            self._create_button(o, buttons_layout, partial(self.window.change_menu, o))
        self._create_button("QUIT", buttons_layout, self.window.close)

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