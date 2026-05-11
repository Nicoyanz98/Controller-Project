from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout

NOTIFICATION_COLOR = {
    "error": ("#FFBABA", "#D8000C"),
    "success": ("#DFF2BF", "#4F8A10"),
    "info": ("#D9EDF7", "#31708F"),
    "warning": ("#FEEFB3", "#9F6000"),
}

class SideNotification(QWidget):
    def __init__(self, message, type):
        super().__init__()

        bg_color, text_color = NOTIFICATION_COLOR[type]

        self.setStyleSheet(
            f"""
            background-color: {bg_color};
            color: {text_color};
            border-radius: 5px;
            padding: 10px;
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        label = QLabel(message)

        layout.addWidget(label)

        QTimer.singleShot(3000, self.close)