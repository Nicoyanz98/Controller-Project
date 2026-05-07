import time
import mediapipe as mp
from mediapipe.tasks.python import vision

from workers.worker import YOLOWorker

class HandsWorker(YOLOWorker):
    detection = None

    def __init__(self, frame_time, context):
        super().__init__(frame_time, context)
        options = vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path="models/hand_landmarker.task"),
            running_mode=vision.RunningMode.IMAGE,
            # min_hand_detection_confidence=0.5,
            # min_hand_presence_confidence=0.5,
            # min_tracking_confidence=0.5,
            num_hands=2
        )
        self.hand_recognizer = vision.HandLandmarker.create_from_options(options)

    def _detect_hands(self, frame):
        mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        self.detection = self.hand_recognizer.detect(mp_frame)

    def run(self):
        last_detection_time = time.time()

        while self.context.is_running():
            current_time = time.time()
            if current_time - last_detection_time >= self.frame_time:
                frame_copy = self.get_current_frame()
                if frame_copy is not None:

                    self._detect_hands(frame_copy)
                    # self.draw_landmarks(frame_copy)

                    self.context.update_mutex_value(self.thread_name, self.detection)
                    last_detection_time = current_time
            else:
                time.sleep(0.01)