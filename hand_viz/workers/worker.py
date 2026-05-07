from abc import ABC, abstractmethod

class YOLOWorker(ABC):
    def __init__(self, context, frame_time, worker_name):
        self.context = context
        self.frame_time = frame_time
        self.worker_name = worker_name
    
    @abstractmethod
    def run(self):
        pass
    