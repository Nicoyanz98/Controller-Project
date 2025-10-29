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
        
        self.distance = (0, 0)
        self.movement = False
        self.start_pos = None

        self.last_move = None
    
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

    def _draw_hand_keypoints(self, hand_landmark):
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

    def draw_keypoints_on_image(self, detection_result: vision.GestureRecognizerResult):
        try:
            top_gesture = detection_result.gestures[0][0]
            hand_landmarks = detection_result.hand_landmarks

            for hand_landmark in hand_landmarks:
                self._draw_hand_keypoints(hand_landmark)
            
            title = f"{top_gesture.category_name} ({top_gesture.score:.2f})"
            height, width, _ = self.frame.shape
            text_x = int(hand_landmarks[0][0].x * width) - 100
            text_y = int(hand_landmarks[0][0].y * height) + 50
            
            cv2.putText(self.annotated_frame, title, (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,255), 2, cv2.LINE_4)

            if top_gesture.category_name == "Pointing_Up":
                self._draw_movement(hand_landmark[8])
            else:
                self.movement = False
                self.distance = (0, 0)
        except:
            self.movement = False
            self.distance = (0, 0)
            pass

    def _draw_movement(self, fingertip_landmark):
        height, width, _ = self.frame.shape
        x = int(fingertip_landmark.x * width)
        y = int(fingertip_landmark.y * height)

        if self.movement:
            self.distance = (x - self.start_pos[0], y - self.start_pos[1])
        else:
            self.movement = True
            self.start_pos = (x, y)
            self.distance = (0, 0)
        
        cv2.circle(self.annotated_frame, self.start_pos, 7, (255,0,255), 2)
        cv2.arrowedLine(self.annotated_frame, self.start_pos, (x, y), (255,0,255), 2)

    def show_movement(self, threshold=0):
        if self.movement:
            cv2.circle(self.annotated_frame, self.start_pos, threshold, (255,0,255), 2)
        moves = []
        if abs(self.distance[1]) > threshold:
            if self.distance[1] > 0:
                moves += ["Down"]
            else:
                moves += ["Up"]
        if abs(self.distance[0]) > threshold:
            if self.distance[0] > 0:
                moves += ["Right"]
            else:
                moves += ["Left"]
        if moves:
            cv2.putText(self.annotated_frame, f"{' '.join(moves)}", (50, 50), cv2.FONT_HERSHEY_DUPLEX, 1, (0,255,255), 2, cv2.LINE_4)