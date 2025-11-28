from ultralytics.engine.results import Results, Boxes
import cv2
import time
import numpy as np
import torch
from abc import ABC, abstractmethod

class YOLODetectorThread(ABC):
    def __init__(self, YOLODetector):
        self.context = YOLODetector
    
    @abstractmethod
    def run(self):
        pass

class CameraThread(YOLODetectorThread):
    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        last_capture_time = time.time()

        while self.context.running:
            current_time = time.time()

            #Limitamos FPS en la camara
            if current_time - last_capture_time >= self.context.frame_time:
                ret, frame = cap.read()
                if ret:
                    with self.context.lock: #PERMITIMOS QUE SOLO UN HILO TRABAJE CON EL FRAME ACTUAL
                        self.context.current_frame = frame.copy() #Copiamos el frame para que solo se trabaje con este

                last_capture_time = current_time
            else:
                time.sleep(0.001) #Permite que no consuma todo el nucleo
        cap.release()

class DetectionThread(YOLODetectorThread):
    tracker = None
    tracks = []
    MAX_STRIDE = 5
    MOTION_THRESH = 50
    AREA_THRESH = 1.1
    COV_INCREASE = 1.1
    results = None

    def interpolate(self, frame, path):
        self.tracker = self.context.model.predictor.trackers[0]
        self.tracks = [t for t in self.tracker.tracked_stracks if t.is_activated]
        
        # Apply Kalman Filter to get predicted locations
        self.tracker.multi_predict(self.tracks)
        self.tracker.frame_id += 1
        
        boxes = np.array([np.hstack([np.array(t.xyxy).reshape(-1), t.track_id, t.score, t.cls]) for t in self.tracks])
        
        # Update frame_id in tracks
        for t in self.tracks:
            t.frame_id = self.tracker.frame_id
        
        if len(self.tracks) == 0:
            tensor = torch.zeros((0,6))
        else:
            tensor = torch.from_numpy(boxes)

        self.results = Results(frame, path, self.context.model.names, boxes=tensor)

    def check_stability_with(self, prev_boxes, prev_tracks):
        curr_boxes = self.results.boxes.xyxy.numpy()
        if len(curr_boxes) == 0 or len(prev_boxes) != len(curr_boxes):
            return False
    
        if len(prev_tracks) == 0 or len(prev_tracks) != len(self.tracks):
            return False
        
        for prev, curr in zip(prev_boxes, curr_boxes):
            # 1. motion constraint
            motion = np.linalg.norm(curr[:2] - prev[:2])
            if motion > self.MOTION_THRESH:
                return False

            # 2. area stability
            prev_area = (prev[2]-prev[0])*(prev[3]-prev[1])
            curr_area = (curr[2]-curr[0])*(curr[3]-curr[1])
            if curr_area > prev_area * self.AREA_THRESH or curr_area < prev_area / self.AREA_THRESH:
                return False

        for prev, curr in zip(prev_tracks, self.tracks):
            # 3. covariance trace
            if np.trace(curr.covariance) > np.trace(prev.covariance) * self.COV_INCREASE:
                return False

        return True

    def make_following(self, frame_copy):
        prev_boxes = self.results.boxes.xyxy.numpy()
        prev_tracks = self.tracks
        
        self.interpolate(frame_copy, self.results.path)

        self.is_following_stable = self.check_stability_with(prev_boxes, prev_tracks)

    def make_inference(self, frame_copy):
        inference = self.context.model.track(
            frame_copy, 
            imgsz=320, 
            conf=0.5, 
            verbose=False,
            persist=True,
            tracker="bytetracker.yaml"
        )
        if inference:
            self.results = inference[0]

    def run(self):
        last_detection_time = time.time()
        frames_since_detection = 0
        is_trackable = False

        while self.context.running:
            current_time = time.time()

            #Limitamos FPS en la deteccion
            if current_time - last_detection_time >= self.context.frame_time:
                if self.context.current_frame is not None:
                    with self.context.lock:
                        frame_copy = self.context.current_frame.copy() #Tomamos una copia para trabajar con el

                    if is_trackable and self.results is not None:
                        # Try to follow boxes without inference
                        self.make_following(frame_copy)
                        
                        if self.is_following_stable and frames_since_detection < self.MAX_STRIDE:
                            frames_since_detection += 1
                        else:
                            is_trackable = False
                    
                    if not is_trackable:
                        # Procesar detección
                        self.make_inference(frame_copy)

                        is_trackable = True
                        frames_since_detection = 0
                    
                    # Actualizar resultados
                    with self.context.lock:
                        self.context.current_results = self.results
                    last_detection_time = current_time
            else:
                time.sleep(0.01)