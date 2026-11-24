import mediapipe as mp
import numpy as np
from mediapipe.tasks.python.components.containers.landmark import NormalizedLandmark
from time import time

from hand.hand_segmenter import HandSegmenter
from utils import HandDataMutex, OneEuroFilter

mp_draw = mp.tasks.vision.drawing_utils
HAND_CONNECTIONS = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS

CALIBRATION_DISTANCE_METERS = 0.5
calibration_constant = None


def convert_rgb_frame_to_mediapipe_frame(rgb_frame):
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

class HandInferencer:
    def __init__(self, hand_detection_mutex: HandDataMutex, model_path='./hand_landmarker.task', use_filter=True):
        self.model_path = model_path
        self.hand_detection_mutex = hand_detection_mutex
        self.use_filter = use_filter
        self.segmenter = HandSegmenter()

        self.filters = {}
        # One Euro Filter Hyperparameters
        self.min_cutoff = 2.5 # Increase if laggy; decrease if jittery at rest
        self.beta = 1.5 # Increase to reduce lag during fast movements

        self._initialize_model()

    def _initialize_model(self):
        self.BaseOptions = mp.tasks.BaseOptions
        self.HandLandmarker = mp.tasks.vision.HandLandmarker
        self.HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        self.VisionRunningMode = mp.tasks.vision.RunningMode

        self.options = self.HandLandmarkerOptions(
            base_options=self.BaseOptions(model_asset_path=self.model_path),
            running_mode=self.VisionRunningMode.LIVE_STREAM,
            num_hands=2,
            min_tracking_confidence=0.5,
            min_hand_presence_confidence=0.6,
            min_hand_detection_confidence=0.6,
            result_callback=self._save_hand_landmarks
        )

        self.model = self.HandLandmarker.create_from_options(self.options)

    def _apply_filter_to_landmarks(self, handedness, hand_landmarks, t_sec, use_filter):
        if not use_filter:
            return hand_landmarks

        if handedness not in self.filters:
            self.filters[handedness] = []
            for landmark in hand_landmarks:
                self.filters[handedness].append(OneEuroFilter(t0=t_sec, x0=[landmark.x, landmark.y, landmark.z], min_cutoff=self.min_cutoff, beta=self.beta))
        
        filtered_landmarks = []
        for landmark_idx, landmark in enumerate(hand_landmarks):
            smoothed = self.filters[handedness][landmark_idx](t_sec, [landmark.x, landmark.y, landmark.z])
            smoothed_landmark = NormalizedLandmark(*smoothed[:3], visibility=landmark.visibility, presence=landmark.presence)
            filtered_landmarks.append(smoothed_landmark)
        return filtered_landmarks

    def _save_hand_landmarks(self, result, input_frame, timestamp_ms):
        if result.hand_landmarks:
            found_hands = self._extract_hand_data(result, input_frame, timestamp_ms)

            self.hand_detection_mutex.clear(keep=found_hands)
            self.filters = {side: self.filters[side] for side in found_hands if side in self.filters}
        else:
            self.hand_detection_mutex.clear()
            self.filters.clear()

    def _extract_hand_data(self, result, input_frame, timestamp_ms):
        found_hands = []
        t_sec = timestamp_ms / 1000.0
        for idx, (hand_landmarks, hand_world_landmarks) in enumerate(zip(result.hand_landmarks, result.hand_world_landmarks)):
            handedness = result.handedness[idx][0].display_name
            found_hands.append(handedness)

            filtered_landmarks = self._apply_filter_to_landmarks(handedness, hand_landmarks, t_sec, self.use_filter)
            segments = self.segmenter.infer(input_frame.numpy_view(), filtered_landmarks)

            self.hand_detection_mutex.save_result(handedness, ([filtered_landmarks, hand_world_landmarks], segments))
        return found_hands

    def infer(self, mp_image):
        self.model.detect_async(mp_image, int(time() * 1000))

    def draw_hand_landmarks(self, frame, hand_landmarks, segments, handedness):
        self.segmenter.draw_segment(frame, segments, handedness)
        mp_draw.draw_landmarks(
            frame,
            hand_landmarks,
            HAND_CONNECTIONS,
            mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_draw.DrawingSpec(color=(0, 0, 255), thickness=2)
        )
        return int(hand_landmarks[0].x * frame.shape[1]), int(hand_landmarks[0].y * frame.shape[0])

    def extract_3d_points(self, frame, world_landmarks, hand_landmarks):
        h, w = frame.shape[:2]
        points = np.array([[landmark.x * w, landmark.y * h] for landmark in hand_landmarks], dtype=np.float32)
        px_dist = np.linalg.norm(points[0] - points[5])
        global calibration_constant
        if calibration_constant is None:
            calibration_constant = px_dist

        absolute_z = calibration_constant * CALIBRATION_DISTANCE_METERS / px_dist
        scale_factor = w
        root = ((points[0] - 0.5) * absolute_z * np.array([w, h])) / scale_factor
        absolute_points = []
        for pt in world_landmarks:
            abs_x = root[0] + pt.x
            abs_y = root[1] + pt.y
            abs_z = absolute_z + pt.z
            absolute_points.append([abs_x, abs_y, abs_z])
        return np.array(absolute_points)

    @staticmethod
    def hand_connections_arr():
        lines = []
        for connection in HAND_CONNECTIONS:
            lines.extend([2, connection.start, connection.end])
        return np.array(lines, dtype=np.int32)