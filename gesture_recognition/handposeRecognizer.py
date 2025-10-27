
import mediapipe as mp
from mediapipe.tasks.python import vision
# from mediapipe.tasks.python.vision import GestureRecognizer, GestureRecognizerOptions, GestureRecognizerResult, RunningMode

import os, time

__all__ = ["Handpose_Recognizer"]

MODEL_PATH = os.path.abspath("./model/gesture_recognizer.task")

class Handpose_Recognizer:
    def __init__(self):
        self.result = vision.GestureRecognizerResult
        self.recognizer = vision.GestureRecognizer
        self.create_recognizer()
    
    def create_recognizer(self):
        def update_result(result: vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
            self.result = result
        
        options = vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=vision.RunningMode.LIVE_STREAM,
            num_hands=1,
            min_hand_detection_confidence=0.4,
            min_hand_presence_confidence=0.4,
            min_tracking_confidence=0.4,
            result_callback=update_result
        )

        self.recognizer = self.recognizer.create_from_options(options)
    
    def recognize_async(self, frame):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        self.recognizer.recognize_async(image=mp_image, timestamp_ms=int(time.time() * 1000))
    
    def close(self):
        self.recognizer.close()