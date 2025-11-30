from abc import ABC, abstractmethod

class YOLODetectorThread(ABC):
    def __init__(self, YOLODetector):
        self.context = YOLODetector
    
    @abstractmethod
    def run(self):
        pass