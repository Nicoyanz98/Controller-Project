from abc import abstractmethod
from PySide6.QtCore import QThread, Signal

class Thread_Task(QThread):
    error_signal = Signal(str)
    success_signal = Signal(str)

    def __init__(self, parent, name):
        super().__init__(parent)
        self._run_flag = True
        self.name = name

    @abstractmethod
    def run(self):
        pass

    def stop(self):
        self._run_flag = False
        self.wait()