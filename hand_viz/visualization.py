import cv2
import threading
import time
import os

from threads import CameraThread, DetectionThread

MODELS_DIR = os.path.join("./models")

class MutexValue():
    def __init__(self):
        self.lock = threading.Lock()
        self.value = None

    def update(self, new_value):
        with self.lock:
            self.value = new_value

    def get(self):
        copy = None
        with self.lock:
            copy = self.value
        
        return copy

class JoystickDetector:
    def __init__(self):

        self.running = True

        self.mutex = {
            "current_frame": MutexValue(),
            "controller": MutexValue(),
            "hands": MutexValue()
        }

        self.target_fps = 30  
        self.frame_time = 1.0 / self.target_fps

        self.fps_count = 0
        self.fps = 0

        self.threads = {
            "camera": CameraThread(self), 
            "controller": DetectionThread(self, f"{MODELS_DIR}/controller_model.pt", "controller", max_stride=1),
            "hands": DetectionThread(self, f"{MODELS_DIR}/hand_model.pt", "hands", max_stride=1),
        }

        self.start_thread("camera")
        self.start_thread("controller")
        self.start_thread("hands")

    def display_boxes(self, display_frame, detection_name):
        current_results = self.mutex[detection_name].get()
        
        if (current_results is not None and current_results.boxes is not None and len(current_results.boxes) > 0):
            boxes = current_results.boxes.xyxy.cpu().numpy()
            classes = current_results.boxes.cls.cpu().numpy()
            confidences = current_results.boxes.conf.cpu().numpy()
            
            for _, (box, class_id, confidence) in enumerate(zip(boxes, classes, confidences)):
                x1, y1, x2, y2 = map(int, box)
                class_id = int(class_id)
                class_name = self.threads[detection_name].model.names[class_id]
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

    def start_thread(self, name):
        thread = threading.Thread(target=self.threads[name].run)
        thread.daemon = True
        thread.start()

    def run(self):
        self.fps_time = time.time()
        last_display_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            if current_time - last_display_time >= self.frame_time:
                last_display_time = current_time

                #Dibujamos el frame actual
                current_frame = self.mutex["current_frame"].get()
                if current_frame is not None:
                    display_frame = current_frame.copy()
                    # Detection Boxes
                    self.display_boxes(display_frame, "controller")
                    self.display_boxes(display_frame, "hands")

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
    detector = JoystickDetector()
    detector.run()
