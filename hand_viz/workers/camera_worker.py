import cv2
import time

from workers.worker import YOLOWorker

class CameraWorker(YOLOWorker):
    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        last_capture_time = time.time()

        while self.context.is_running():
            current_time = time.time()

            #Limitamos FPS en la camara
            if current_time - last_capture_time >= self.frame_time:
                ret, frame = cap.read()
                if ret:
                    self.context.update_mutex_value(self.worker_name, frame.copy()) #Copiamos el frame para que solo se trabaje con este

                last_capture_time = current_time
            else:
                time.sleep(0.001)
        cap.release()