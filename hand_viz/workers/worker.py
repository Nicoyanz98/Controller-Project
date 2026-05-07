from abc import ABC, abstractmethod

class YOLOWorker(ABC):
    def __init__(self, frame_time, context):
        self.context = context
        self.frame_time = frame_time
    
    @abstractmethod
    def run(self):
        pass
    