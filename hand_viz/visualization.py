from ultralytics import YOLO
import cv2
import threading
import time
from threads import CameraThread, DetectionThread

class YOLODetector:
    def __init__(self):
        self.model = YOLO("best.pt")
        self.current_frame = None
        self.current_results = None
        self.running = True
        self.lock = threading.Lock()
        self.target_fps = 30  
        self.frame_time = 1.0 / self.target_fps

        self.fps_count = 0
        self.fps = 0

        self.threads = {
            "camera": CameraThread(self), 
            "detection": DetectionThread(self)
        }
    
    def display_boxes(self, display_frame):
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

    def display_fps(self, display_frame, current_time):
        self.fps_count += 1 #Contamos los frames
        if current_time - self.fps_time >= 1.0: #Si paso mas de un segundo, actuazamos el contador
            self.fps = self.fps_count
            self.fps_count = 0
            self.fps_time = current_time
        
        cv2.putText(display_frame, f"FPS: {self.fps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    def run(self):
        #incializamos hilos
        cam_thread = threading.Thread(target=self.threads["camera"].run)
        det_thread = threading.Thread(target=self.threads["detection"].run)
        
        #Damos variable para que inice con el programa y cierre con el mismo
        cam_thread.daemon = True
        det_thread.daemon = True
        cam_thread.start()
        det_thread.start()
        
        
        self.fps_time = time.time()
        last_display_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            if current_time - last_display_time >= self.frame_time:
                last_display_time = current_time

                #Dibujamos el frame acutal
                if self.current_frame is not None:
                    display_frame = self.current_frame.copy()
                    
                    # Boxes
                    self.display_boxes(display_frame)
                    
                    # FPS
                    self.display_fps(display_frame, current_time)

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