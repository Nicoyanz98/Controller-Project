from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt

class ResizableImage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.image_label = QLabel(self)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        
        self.current_pixmap = None

    def set_pixmap(self, pixmap):
        self.current_pixmap = pixmap
        self.update_display()

    def update_display(self):
        if not self.current_pixmap or self.size().isEmpty():
            return
        
        scaled_size = self.current_pixmap.size()
        scaled_size.scale(self.size(), Qt.KeepAspectRatio)

        self.image_label.resize(scaled_size)
        
        scaled_pixmap = self.current_pixmap.scaled(
            scaled_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
            
        self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display()

    def clear(self):
        self.image_label.setStyleSheet("")
        self.image_label.clear()
    
    def toggle_input_feedback(self, pressed):
        if pressed:
            self.image_label.setStyleSheet("""
                QLabel {
                    border: 5px solid green;
                }
            """)
        else:
            self.image_label.setStyleSheet("""
                QLabel {
                    border: 5px solid yellow;
                }
            """)
