import cv2
import numpy as np

from utils import BoxesMutex, HandDataMutex
from hand.hand_inferencer import HandInferencer, convert_rgb_frame_to_mediapipe_frame
from joystick.joystick_boxes_inferencer import JoystickBoxesInferencer
from hand.hand_renderer import Hand3DRenderer

class JoystickInputDetector:
    def __init__(self, hand_detection_mutex: HandDataMutex, boxes_detection_mutex: BoxesMutex, hand_inferencer: HandInferencer, joystick_boxes_inferencer: JoystickBoxesInferencer):
        self.hand_detection_mutex = hand_detection_mutex
        self.boxes_detection_mutex = boxes_detection_mutex
        self.hand_inferencer = hand_inferencer
        self.joystick_boxes_inferencer = joystick_boxes_inferencer
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # self.hand_renderer = Hand3DRenderer(self.hand_inferencer.hand_connections_arr())

        if not self.cap.isOpened():
            raise RuntimeError("Error: Could not open webcam.")

    def _prepare_frame_for_mediapipe(self, frame):
        resize_frame = cv2.resize(frame, (224, 224))
        rgb_frame = cv2.cvtColor(resize_frame, cv2.COLOR_BGR2RGB)
        return convert_rgb_frame_to_mediapipe_frame(rgb_frame)

    def _draw_annotations(self, frame):
        self._draw_boxes(frame)
        self._draw_hands(frame)

    def _draw_hands(self, frame):
        landmarks_and_segments = self.hand_detection_mutex.get_result()
        pts_arr = []
        hands_detected = []
        for handedness, (hand_landmarks, segments) in landmarks_and_segments.items():
            x, y = self.hand_inferencer.draw_hand_landmarks(frame, hand_landmarks[0], segments, handedness)
            cv2.putText(frame, handedness, (x, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            pts_3d = self.hand_inferencer.extract_3d_points(frame, hand_landmarks[1], hand_landmarks[0])
            # print(pts_3d[0])
            # input()
            pts_arr.append(pts_3d)
            hands_detected.append(handedness)

        # self.hand_renderer.render_hands(hands_detected, pts_arr)

    def _draw_boxes(self, frame):
        boxes = self.boxes_detection_mutex.get_result() 
        if boxes is not None:
            self.joystick_boxes_inferencer.draw_boxes(frame, boxes)

    def start(self):
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame.")
                    break

                self.hand_inferencer.infer(self._prepare_frame_for_mediapipe(frame))
                self.joystick_boxes_inferencer.infer(frame)
                self._draw_annotations(frame)
                cv2.imshow('Hand Landmarker', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            # self.hand_renderer.close()
            self.cap.release()
            cv2.destroyAllWindows()
            
