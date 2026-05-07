from abc import ABC, abstractmethod

class YOLOWorker(ABC):
    def __init__(self, context):
        self.context = context
    
    @abstractmethod
    def run(self):
        pass
    