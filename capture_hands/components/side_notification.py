from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QLabel, QWidget

NOTIFICATION_COLOR = {
    "error": "background-color: #FFBABA; color: #D8000C;",
    "success": "background-color: #DFF2BF; color: #4F8A10;",
    "info": "background-color: #D9EDF7; color: #31708F;",
    "warning": "background-color: #FEEFB3; color: #9F6000;",
}

class SideNotification(QWidget):
    def __init__(self, parent, message, type):
        super().__init__(parent)
        self.setStyleSheet(f"{NOTIFICATION_COLOR[type]} border-radius: 5px; padding: 10px;")

        self.notification = QLabel(message, self)

        metrics = QFontMetrics(self.font())
        text_width = metrics.horizontalAdvance(message)
        text_height = metrics.height()
        
        new_width = text_width + 40 
        new_height = text_height + 20
        self.setFixedSize(new_width, new_height)
        
        self.update_position()
        self.show()

        QTimer.singleShot(3000, self.deleteLater)

    def update_position(self):
        if self.parentWidget():
            self.move(20, 20)