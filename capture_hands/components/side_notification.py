from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout
# from PySide6.QtGui import QFontMetrics

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



# from PySide6.QtCore import Qt, QTimer
# from PySide6.QtGui import QFontMetrics
# from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout

# NOTIFICATION_COLOR = {
#     "error": "background-color: #FFBABA; color: #D8000C;",
#     "success": "background-color: #DFF2BF; color: #4F8A10;",
#     "info": "background-color: #D9EDF7; color: #31708F;",
#     "warning": "background-color: #FEEFB3; color: #9F6000;",
# }

# class SideNotification(QWidget):
#     def __init__(self, message, type):
#         super().__init__()
#         self.setStyleSheet(f"{NOTIFICATION_COLOR[type]} border-radius: 5px; padding: 10px;")

#         layout = QHBoxLayout(self)

#         label = QLabel(message)
#         layout.addWidget(label)

#         self.adjustSize()
#         # metrics = QFontMetrics(self.font())
#         # text_width = metrics.horizontalAdvance(message)
#         # text_height = metrics.height()
        
#         # new_width = text_width + 40 
#         # new_height = text_height + 20
#         # self.setFixedSize(new_width, new_height)
        
#         # self.update_position()
#         # self.show()

#         QTimer.singleShot(3000, self.close)