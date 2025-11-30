import time
import mediapipe as mp

from threads import YOLODetectorThread

class HandsThread(YOLODetectorThread):
    detection = None

    def detect_hands(self, frame):
        mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        self.detection = self.context.hand_recognizer.detect(mp_frame)

    def run(self):
        last_detection_time = time.time()

        while self.context.running:
            current_time = time.time()
            if current_time - last_detection_time >= self.context.frame_time:
                if self.context.current_frame is not None:
                    with self.context.frame_lock:
                        frame_copy = self.context.current_frame.copy()

                    self.detect_hands(frame_copy)
                    self.draw_landmarks(frame_copy)

                    with self.context.hands_detection_lock:
                        self.context.hands_detection = self.detection
                    last_detection_time = current_time
            else:
                time.sleep(0.01)