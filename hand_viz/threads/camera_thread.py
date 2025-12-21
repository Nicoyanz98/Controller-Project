import cv2
import time

from threads import YOLODetectorThread

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
                    #PERMITIMOS QUE SOLO UN HILO TRABAJE CON EL FRAME ACTUAL
                    self.mutex["current_frame"].update(frame.copy())#Copiamos el frame para que solo se trabaje con este

                last_capture_time = current_time
            else:
                time.sleep(0.001) #Permite que no consuma todo el nucleo
        cap.release()