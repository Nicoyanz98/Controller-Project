from PySide6.QtCore import QMargins, QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout

class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(QMargins(0, 0, 0, 0))

        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _do_layout(self, rect, test_only):
        spacing = self.spacing()

        rows = []
        current_row = []
        current_width = 0
        line_height = 0

        # Build rows
        for item in self._item_list:
            item_width = item.sizeHint().width()
            item_height = item.sizeHint().height()

            next_width = current_width + item_width + spacing

            if current_row and next_width > rect.width():
                rows.append((current_row, current_width - spacing, line_height))
                current_row = []
                current_width = 0
                line_height = 0

            current_row.append(item)
            current_width += item_width + spacing
            line_height = max(line_height, item_height)

        if current_row:
            rows.append((current_row, current_width - spacing, line_height))

        # Draw centered rows
        y = rect.y()

        for row_items, row_width, row_height in rows:
            x = rect.x() + (rect.width() - row_width) // 2

            for item in row_items:
                if not test_only:
                    item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

                x += item.sizeHint().width() + spacing

            y += row_height + spacing

        return y - rect.y()