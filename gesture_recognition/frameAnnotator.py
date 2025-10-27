import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2

import time, math

__all__ = ["Frame_Annotator"]

class Frame_Annotator:
    def __init__(self):
        self.frame = None
        self.annotated_frame = None
        
        self.prev_time = 0
        
        self.distance = 0
        self.measure = False
        self.prev_pos = None

        self.distance_display_start = 0
        self.saved_distance = None
    
    def update_frame(self, frame):
        self.frame = frame
        self.annotated_frame = frame.copy()

        self._framesCounter()

    def _framesCounter(self):
        _, width, _ = self.frame.shape

        cur_time = time.time()
        fps = 1 / (cur_time - self.prev_time)
        cv2.putText(self.annotated_frame, f'FPS: {int(fps)}', (width-100, 50), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        
        self.prev_time = cur_time

    def draw_keypoints_on_image(self, detection_result: vision.GestureRecognizerResult):
        try:
            top_gesture = detection_result.gestures[0][0]
            hand_landmarks = detection_result.hand_landmarks

            for hand_landmark in hand_landmarks:
                hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
                hand_landmarks_proto.landmark.extend([
                    landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmark
                ])

                mp.solutions.drawing_utils.draw_landmarks(
                    self.annotated_frame,
                    hand_landmarks_proto,
                    mp.solutions.hands.HAND_CONNECTIONS,
                    mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                    mp.solutions.drawing_styles.get_default_hand_connections_style()
                )
            
            title = f"{top_gesture.category_name} ({top_gesture.score:.2f})"
            height, width, _ = self.frame.shape
            text_x = int(hand_landmarks[0][0].x * width) - 100
            text_y = int(hand_landmarks[0][0].y * height) + 50
            
            cv2.putText(self.annotated_frame, title, (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,255), 2, cv2.LINE_4)

            if top_gesture.category_name == "Pointing_Up":
                self._calculate_distance(hand_landmark[8])
                self.measure = True
            
            if top_gesture.category_name == "Closed_Fist" and self.measure:
                self.saved_distance = self.distance

                self.measure = False
                self.distance = 0
                self.prev_pos = None
        except:
            pass

    def _calculate_distance(self, fingertip_landmark):
        height, width, _ = self.frame.shape
        x = int(fingertip_landmark.x * width)
        y = int(fingertip_landmark.y * height)

        if self.prev_pos:
            dx = x - self.prev_pos[0]
            dy = y - self.prev_pos[1]
            self.distance += math.sqrt(dx*dx + dy*dy)
        self.prev_pos = (x, y)

    def show_distance(self, last_distance):
        if self.saved_distance:
            if last_distance != self.saved_distance:
                self.distance_display_start = time.time()
            
            elapsed_time = time.time() - self.distance_display_start
            
            if elapsed_time < 5:
                cv2.putText(self.annotated_frame, f"{self.saved_distance:.2f}px", (50, 50), cv2.FONT_HERSHEY_DUPLEX, 1, (0,255,255), 2, cv2.LINE_4)
            else:
                self.saved_distance = None
        
        return self.saved_distance