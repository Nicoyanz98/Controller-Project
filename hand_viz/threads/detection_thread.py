import time
from ultralytics import YOLO
from ultralytics.engine.results import Results
import numpy as np
import torch

from threads import YOLODetectorThread

MAX_STRIDE = 10
MOTION_THRESH = 5
AREA_THRESH = 1.007
COV_INCREASE = 1.07
MAX_WAIT_FPS = 30

class DetectionThread(YOLODetectorThread):
    tracker = None
    tracks = []
    
    def __init__(self, YOLODetector, model_path, mutex_result_name, max_stride=MAX_STRIDE, motion_thresh=MOTION_THRESH, area_thresh=AREA_THRESH, cov_increase=COV_INCREASE):
        super().__init__(YOLODetector)

        self.mutex_name = mutex_result_name

        self.model = YOLO(model_path)

        self.max_stride = max_stride
        self.motion_thresh = motion_thresh
        self.area_thresh = area_thresh
        self.cov_increase = cov_increase
        self.results = None

        self.max_wait_fps = MAX_WAIT_FPS

    def _interpolate(self, frame, path):
        self.tracker = self.model.predictor.trackers[0]
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

        self.results = Results(frame, path, self.model.names, boxes=tensor)

    def _check_stability_with(self, prev_boxes, prev_tracks):
        curr_boxes = self.results.boxes.xyxy.numpy()
        if len(curr_boxes) == 0 or len(prev_boxes) != len(curr_boxes):
            return False
    
        if len(prev_tracks) == 0 or len(prev_tracks) != len(self.tracks):
            return False
        
        for prev, curr in zip(prev_boxes, curr_boxes):
            # 1. motion constraint
            motion = np.linalg.norm(curr[:2] - prev[:2])
            if motion > self.motion_thresh:
                return False

            # 2. area stability
            prev_area = (prev[2]-prev[0])*(prev[3]-prev[1])
            curr_area = (curr[2]-curr[0])*(curr[3]-curr[1])
            if curr_area > prev_area * self.area_thresh or curr_area < prev_area / self.area_thresh:
                return False

        for prev, curr in zip(prev_tracks, self.tracks):
            # 3. covariance trace
            if np.trace(curr.covariance) > np.trace(prev.covariance) * self.cov_increase:
                return False

        return True

    def _make_following(self, frame_copy):
        prev_boxes = self.results.boxes.xyxy.numpy()
        prev_tracks = self.tracks
        
        self._interpolate(frame_copy, self.results.path)

        self.is_following_stable = self._check_stability_with(prev_boxes, prev_tracks)

    def _make_inference(self, frame_copy):
        inference = self.model.track(
            frame_copy, 
            imgsz=320, 
            conf=0.5, 
            verbose=False,
            persist=True,
            tracker="bytetracker.yaml"
        )
        if inference:
            self.results = inference[0]
            if  len(self.results.boxes) == 0:
                return False
            
        return True

    def run(self):
        last_detection_time = time.time()
        frames_since_detection = 0
        is_trackable = False
        detection = False
        empty_frames = 0

        while self.context.running:
            current_time = time.time()

            #Limitamos FPS en la deteccion
            if current_time - last_detection_time >= self.context.frame_time:
                current_frame = self.context.mutex["current_frame"].get()

                if current_frame is not None:
                    frame_copy = current_frame.copy()
                    if is_trackable and self.results is not None:
                        self._make_following(frame_copy)
                        
                        if self.is_following_stable and frames_since_detection < self.max_stride:
                            frames_since_detection += 1
                        else:
                            is_trackable = False
                    
                    if not is_trackable:
                        # Procesar detección
                        detection = self._make_inference(frame_copy) and self.max_stride > 1
                        frames_since_detection = 0
                        is_trackable = detection
                    
                    # Actualizar resultados
                    self.context.mutex[self.mutex_name].update(self.results)
                    last_detection_time = current_time
                    

                    if detection:
                        empty_frames = 0
                    else:
                        # Esperar si no hay detecciones
                        if empty_frames > (self.max_wait_fps // 2):
                            empty_frames += 1
                        cooldown = min(2 ** empty_frames, self.max_wait_fps) # Exponential wait
                        time.sleep(cooldown * 0.01)
            else:
                time.sleep(0.01)