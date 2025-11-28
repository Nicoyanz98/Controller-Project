from ultralytics import YOLO
from ultralytics.engine.results import Results, Boxes
import cv2
import threading
import time
import numpy as np
import torch


class YOLODetector:
    def __init__(self):
        self.model = YOLO("best.pt")
        self.current_frame = None
        self.current_results = None
        self.running = True
        self.lock = threading.Lock()
        self.target_fps = 30  
        self.frame_time = 1.0 / self.target_fps
        self.tracker = None
        self.tracks = []
        self.MAX_STRIDE = 5
        self.MOTION_THRESH = 50
        self.AREA_THRESH = 1.1
        self.COV_INCREASE = 1.1

    def camera_thread(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        last_capture_time = time.time()

        while self.running:
            current_time = time.time()

            #Limitamos FPS en la camara
            if current_time - last_capture_time >= self.frame_time:
                ret, frame = cap.read()
                if ret:
                    with self.lock: #PERMITIMOS QUE SOLO UN HILO TRABAJE CON EL FRAME ACTUAL
                        self.current_frame = frame.copy() #Copiamos el frame para que solo se trabaje con este

                last_capture_time = current_time
            else:
                time.sleep(0.001) #Permite que no consuma todo el nucleo
        cap.release()

    def update_tracks(self):
        self.tracker = self.model.predictor.trackers[0]
        self.tracks = [t for t in self.tracker.tracked_stracks if t.is_activated]

    # Tracking without inference
    def interpolate(self, frame, path):
        self.update_tracks()
        # Apply Kalman Filter to get predicted locations
        self.tracker.multi_predict(self.tracks)
        self.tracker.frame_id += 1
        
        boxes = np.array([np.hstack([np.array(t.xyxy).reshape(-1), t.track_id, t.score, t.cls]) for t in self.tracks])
        tensor = torch.from_numpy(boxes)
        
        # Update frame_id in tracks
        for t in self.tracks:
            t.frame_id = self.tracker.frame_id
        
        if len(self.tracks) == 0:
            tensor = torch.zeros((0,6))
        return Results(frame, path, self.model.names, boxes=tensor)

    def is_stable(self, prev_boxes, curr_boxes, prev_tracks):
        if len(curr_boxes) == 0 or len(prev_boxes) != len(curr_boxes):
            return False
    
        if len(prev_tracks) == 0 or len(prev_tracks) != len(self.tracks):
            return False
        
        for prev, curr, prev_t, curr_t in zip(prev_boxes, curr_boxes, prev_tracks, self.tracks):
            # 1. motion constraint
            motion = np.linalg.norm(curr[:2] - prev[:2])
            if motion > self.MOTION_THRESH:
                return False

            # 2. area stability
            prev_area = (prev[2]-prev[0])*(prev[3]-prev[1])
            curr_area = (curr[2]-curr[0])*(curr[3]-curr[1])
            if curr_area > prev_area * self.AREA_THRESH or curr_area < prev_area / self.AREA_THRESH:
                return False

            # 3. covariance trace
            if np.trace(curr_t.covariance) > np.trace(prev_t.covariance) * self.COV_INCREASE:
                return False

        return True

    def detection_thread(self):
        last_detection_time = time.time()
        frames_since_detection = 0
        results = []
        is_trackable = False

        while self.running:
            current_time = time.time()

            #Limitamos FPS en la deteccion
            if current_time - last_detection_time >= self.frame_time:
                if self.current_frame is not None:
                    with self.lock:
                        frame_copy = self.current_frame.copy() #Tomamos una copia para trabajar con el

                    if is_trackable and results is not None:
                        prev_boxes = results.boxes.xyxy.numpy()
                        prev_tracks = self.tracks
                        results = self.interpolate(frame_copy, results.path)
                        stable = self.is_stable(prev_boxes, results.boxes.xyxy.numpy(), prev_tracks)
                        # print(stable)
                        if stable and frames_since_detection < self.MAX_STRIDE:
                            frames_since_detection += 1
                        else:
                            is_trackable = False
                    
                    if not is_trackable:
                        # Procesar detección
                        results = self.model.track(
                            frame_copy, 
                            imgsz=320, 
                            conf=0.5, 
                            verbose=False,
                            persist=True,
                            tracker="bytetracker.yaml"
                        )
                        if results:
                            results = results[0]
                        is_trackable = True
                        frames_since_detection = 0
                    
                    # Actualizar resultados
                    with self.lock:
                        self.current_results = results
                    last_detection_time = current_time
            else:
                time.sleep(0.01)

    def run(self):
        #incializamos hilos
        cam_thread = threading.Thread(target=self.camera_thread)
        det_thread = threading.Thread(target=self.detection_thread)
        
        #Damos variable para que inice con el programa y cierre con el mismo
        cam_thread.daemon = True
        det_thread.daemon = True
        cam_thread.start()
        det_thread.start()
        
        fps_count = 0
        fps = 0
        fps_time = time.time()
        last_display_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            if current_time - last_display_time >= self.frame_time:
                last_display_time = current_time

                #Dibujamos el frame acutal
                if self.current_frame is not None:
                    display_frame = self.current_frame.copy()
                    
                    
                    if (self.current_results is not None and self.current_results.boxes is not None and len(self.current_results.boxes) > 0):
                        
                        boxes = self.current_results.boxes.xyxy.cpu().numpy()
                        classes = self.current_results.boxes.cls.cpu().numpy()
                        confidences = self.current_results.boxes.conf.cpu().numpy()
                        
                        for _, (box, class_id, confidence) in enumerate(zip(boxes, classes, confidences)):
                            x1, y1, x2, y2 = map(int, box)
                            class_id = int(class_id)
                            class_name = self.model.names[class_id]
                            confidence = float(confidence)
                            
                            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            label = f"{class_name}: {confidence:.2f}"
                            cv2.putText(display_frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    # FPS
                    fps_count += 1 #Contamos los frames
                    if current_time - fps_time >= 1.0: #Si paso mas de un segundo, actuazamos el contador
                        fps = fps_count
                        fps_count = 0
                        fps_time = current_time
                    
                    cv2.putText(display_frame, f"FPS: {fps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    cv2.imshow("Detector de joystick", display_frame)

            time.sleep(0.001)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                self.running = False
                break
        
        cv2.destroyAllWindows()


if __name__ == "__main__":
    detector = YOLODetector()
    detector.run()