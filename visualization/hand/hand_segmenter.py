import cv2
import numpy as np
from mediapipe.tasks.python.vision.hand_landmarker import HandLandmarksConnections

COLOR = {
    'Left': (0, 255, 128),
    'Right': (255, 0, 128)
}

CONNECTIONS = [(connection.start,connection.end) for connection in HandLandmarksConnections.HAND_CONNECTIONS]
PALM_POINTS = list({x for conn in HandLandmarksConnections.HAND_PALM_CONNECTIONS for x in (conn.start, conn.end)})

# Based on https://github.com/itap-robotica-medica/lightweight-hand-segmentation/blob/main/hand_segmentation.py
class HandSegmenter:
    def __init__(self, std_factor=2.0):
        self.std_factor = std_factor

    def _landmarks_to_np_array(self, hand_landmarks, h, w):
        return np.array([[int(lm.x * w), int(lm.y * h)] for lm in hand_landmarks], dtype=np.int32)

    def _get_m1_skeleton_mask(self, shape, points, line_thickness):
        m1 = np.zeros(shape[:2], dtype=np.uint8)
        cv2.drawContours(m1, points[CONNECTIONS].astype(np.int32), -1, 255, thickness=line_thickness)
        cv2.drawContours(m1, points[:, None, :].astype(np.int32), -1, 255, line_thickness)

        cv2.fillConvexPoly(m1, cv2.convexHull(points[PALM_POINTS]), 255)

        return m1

    def _get_mask_ab(self, skin_pixels, img_lab, m2_mask=None):
        mean = np.mean(skin_pixels, axis=0)
        std = np.std(skin_pixels, axis=0)

        lower_bound = np.clip(mean - self.std_factor * std, 0, 255).astype(np.uint8)
        upper_bound = np.clip(mean + self.std_factor * std, 0, 255).astype(np.uint8)

        mask_a = cv2.inRange(img_lab[:,:,1], int(lower_bound[1]), int(upper_bound[1]))
        mask_b = cv2.inRange(img_lab[:,:,2], int(lower_bound[2]), int(upper_bound[2]))

        return cv2.bitwise_and(mask_a, mask_b, mask=m2_mask)

    def _get_hand_scale(self, points):
        palm_dist = np.linalg.norm(points[0] - points[9])
        return max(palm_dist, 10.0)

    def _create_kernels(self, palm_scale):
        m2_kernel_size = max(3, int(palm_scale * 0.15) | 1)
        morph_kernel_size = max(3, int(palm_scale * 0.08) | 1)
        dilate2_kernel_size = max(3, int(palm_scale * 0.04) | 1)

        self.kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (m2_kernel_size, m2_kernel_size))
        self.kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_kernel_size, morph_kernel_size))
        self.kernel_dilate2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate2_kernel_size, dilate2_kernel_size))

    def infer(self, frame_rgb, hand_landmarks):
        h, w, _ = frame_rgb.shape
        points = self._landmarks_to_np_array(hand_landmarks, h, w)

        palm_scale = self._get_hand_scale(points)
        m1_thickness = max(2, int(palm_scale * 0.05))
        self._create_kernels(palm_scale)
        
        # Create spatial masks M1 (skeleton sample) and M2 (M1 dilation)
        m1_mask = self._get_m1_skeleton_mask((h, w), points, m1_thickness)
        m2_mask = cv2.dilate(m1_mask, self.kernel_dilate, iterations=2)

        frame_lab = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2LAB)

        skin_pixels = frame_lab[m1_mask == 255]
        if len(skin_pixels) == 0:
            return m2_mask

        # Mask based on skin color in Lab space
        mask_ab = self._get_mask_ab(skin_pixels, frame_lab, m2_mask)

        # Morphological processing (Close -> Open -> Dilate)
        segmented_mask = cv2.morphologyEx(mask_ab, cv2.MORPH_CLOSE, self.kernel_close)
        segmented_mask = cv2.morphologyEx(segmented_mask, cv2.MORPH_OPEN, self.kernel_close)
        segmented_mask = cv2.dilate(segmented_mask, self.kernel_dilate2, iterations=1)

        # Mask with M2 to ensure the segmentation is within the hand region
        segmented_mask = cv2.bitwise_and(segmented_mask, segmented_mask, mask=m2_mask)

        return segmented_mask

    def draw_segment(self, frame, segments, handedness, alpha=0.4):
        if segments is None:
            return

        if segments.shape[:2] != frame.shape[:2]:
            segments = cv2.resize(segments, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)

        overlay = frame.copy()
        overlay[segments == 255] = COLOR[handedness]
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)