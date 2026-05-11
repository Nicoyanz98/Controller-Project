from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from components import SideNotification


class NotificationContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_StyledBackground, False)

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.resize(300, 600)

        self.move(20, 20)
        
        self.show()

    def add_notification(self, message, type):
        notification = SideNotification(message, type)

        self.layout.addWidget(notification)

        notification.show()