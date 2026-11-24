from joystick.async_YOLO import AsyncYOLO
from utils import BoxesMutex
import cv2
import numpy as np

class JoystickBoxesInferencer:
    def __init__(self, boxes_mutex: BoxesMutex, model_path='./joystick_yolo_v2.pt'):
        self.model_path = model_path
        self.boxes_mutex = boxes_mutex
        self._initialize_model()

    def _initialize_model(self):
        self.model = AsyncYOLO(self.model_path, callback_fn=self._save_boxes)
        self.model.start()
        self.boxes_mutex.clear()

    def _save_boxes(self, result):
        self.boxes_mutex.save_results(result)

    def infer(self, frame):
        self.model.track_async(frame)

    def draw_boxes(self, frame, result):
        names = result.names
        boxes = result.boxes
        for score, cl, bbox in zip(boxes.conf.numpy(), boxes.cls.numpy(), boxes.xyxy.numpy()):
            label = f"{names[cl]}: {score:0.2f}"
            lbl_margin = 3
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), color=(0,0,255), thickness=1)
            cv2.putText(frame, label, (int(bbox[0]) + lbl_margin, int(bbox[1]) - lbl_margin), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(0, 0, 255), thickness=0)