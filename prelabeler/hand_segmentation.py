import sys
import importlib
from pathlib import Path

import cv2
import numpy as np

from hand_slots import N_SLOTS

# Part ids of the hand masks: 0 background, 1 palm ... 6 pinky
PART_NAMES = ["palm", "thumb", "index", "middle", "ring", "pinky"]
PART_IDS = {name: idx + 1 for idx, name in enumerate(PART_NAMES)}
N_PARTS = len(PART_NAMES)

FINGER_CHAINS = {
    PART_IDS["thumb"]: [1, 2, 3, 4],
    PART_IDS["index"]: [5, 6, 7, 8],
    PART_IDS["middle"]: [9, 10, 11, 12],
    PART_IDS["ring"]: [13, 14, 15, 16],
    PART_IDS["pinky"]: [17, 18, 19, 20],
}
PALM_POINTS = [0, 1, 5, 9, 13, 17]
# MediaPipe HAND_CONNECTIONS
HAND_CONNECTIONS = [
    (0, 1), (0, 17), (1, 2), (2, 3), (3, 4), (1, 5), (5, 6), (6, 7),
    (7, 8), (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
    (15, 16), (13, 17), (17, 18), (18, 19), (19, 20),
]
# Finger width as a fraction of the hand scale (wrist -> middle finger MCP)
FINGER_WIDTH = {
    PART_IDS["thumb"]: 0.30,
    PART_IDS["index"]: 0.24,
    PART_IDS["middle"]: 0.25,
    PART_IDS["ring"]: 0.23,
    PART_IDS["pinky"]: 0.20,
}


class LandmarkHandSegmenter:
    """Approximate hand part mask from the 21 landmarks: filled palm polygon plus thick
    lines along each finger.

        width_scale  multiplies all finger widths (tune per camera distance)
        palm_expand  grows the palm polygon, landmarks sit at joint centres, not the skin edge
        tip_extend   extends each fingertip along its last bone (fraction of that bone)
    """

    def __init__(self, width_scale=1.0, palm_expand=1.15, tip_extend=0.25):
        self.width_scale = width_scale
        self.palm_expand = palm_expand
        self.tip_extend = tip_extend

    def params(self):
        return {"width_scale": self.width_scale, "palm_expand": self.palm_expand, "tip_extend": self.tip_extend}

    def infer(self, shape_hw, landmarks):
        """Returns the (h, w) uint8 part id mask of the normalized landmarks (zeros if invalid)."""
        h, w = shape_hw[:2]
        mask = np.zeros((h, w), np.uint8)
        landmarks = np.asarray(landmarks, dtype=np.float64)
        if landmarks.shape[0] != 21 or not np.isfinite(landmarks[:, :2]).all():
            return mask

        points = landmarks[:, :2] * np.array([w, h])
        scale = float(np.linalg.norm(points[0] - points[9]))
        if scale < 2:
            return mask

        palm = points[PALM_POINTS]
        center = palm.mean(0)
        palm = center + (palm - center) * self.palm_expand
        hull = cv2.convexHull(np.round(palm).astype(np.int32))
        cv2.fillConvexPoly(mask, hull, PART_IDS["palm"], lineType=cv2.LINE_8)

        for part, chain_ids in FINGER_CHAINS.items():
            width = max(int(round(FINGER_WIDTH[part] * scale * self.width_scale)), 1)
            chain = points[chain_ids]
            tip = chain[-1] + (chain[-1] - chain[-2]) * self.tip_extend
            chain = np.round(np.vstack([chain, tip])).astype(np.int32)

            # LINE_8, never LINE_AA: anti-aliasing would blend part ids
            for idx in range(len(chain) - 1):
                start = tuple(map(int, chain[idx]))
                end = tuple(map(int, chain[idx + 1]))
                cv2.line(mask, start, end, part, thickness=width, lineType=cv2.LINE_8)
            for point in chain:
                cv2.circle(mask, tuple(map(int, point)), max(width // 2, 1), part, -1, cv2.LINE_8)
        return mask


class SkinHandSegmenter:
    """Skin colour hand segmentation guided by the landmarks
    (based on itap-robotica-medica/lightweight-hand-segmentation):
        - a thin skeleton (bones, joints and palm) samples the skin colour
        - the dilated skeleton is the region where the hand can be
        - pixels within std_factor deviations of the skin colour in Lab a/b (L ignored,
          robust to lighting) are kept, then cleaned with close -> open -> dilate

        std_factor  colour tolerance, raise if fingers get cut, lower if background leaks in
        robust      median/MAD instead of mean/std, less pulled by controller pixels
                    sampled where a finger is occluded
    """

    def __init__(self, std_factor=2.0, robust=False):
        self.std_factor = std_factor
        self.robust = robust
        self.connections = np.array(HAND_CONNECTIONS)

    def params(self):
        return {"std_factor": self.std_factor, "robust": self.robust}

    def _kernel(self, size):
        return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))

    def infer(self, frame_rgb, landmarks, frame_lab=None):
        """Returns the (h, w) uint8 hand mask (255 = hand). frame_lab can be reused for both hands."""
        h, w = frame_rgb.shape[:2]
        landmarks = np.asarray(landmarks, dtype=np.float64)
        if landmarks.ndim != 2 or landmarks.shape[0] != 21 or not np.isfinite(landmarks[:, :2]).all():
            return np.zeros((h, w), np.uint8)
        points = (landmarks[:, :2] * np.array([w, h])).astype(np.int32)

        scale = max(float(np.linalg.norm(points[0] - points[9])), 10.0)
        thickness = max(2, int(scale * 0.05))
        dilate_kernel = self._kernel(max(3, int(scale * 0.15) | 1))
        close_kernel = self._kernel(max(3, int(scale * 0.08) | 1))
        final_kernel = self._kernel(max(3, int(scale * 0.04) | 1))

        # Skeleton sample and search region
        skeleton = np.zeros((h, w), np.uint8)
        cv2.drawContours(skeleton, points[self.connections], -1, 255, thickness=thickness)
        cv2.drawContours(skeleton, points[:, None, :], -1, 255, thickness)
        cv2.fillConvexPoly(skeleton, cv2.convexHull(points[PALM_POINTS]), 255)
        region = cv2.dilate(skeleton, dilate_kernel, iterations=2)

        if frame_lab is None:
            frame_lab = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2LAB)
        sample = frame_lab[skeleton == 255].astype(np.float32)
        if len(sample) == 0:
            return region

        # Skin colour model
        if self.robust:
            center = np.median(sample, axis=0)
            spread = 1.4826 * np.median(np.abs(sample - center), axis=0)
        else:
            center = sample.mean(0)
            spread = sample.std(0)
        low = np.clip(center - self.std_factor * spread, 0, 255).astype(np.uint8)
        high = np.clip(center + self.std_factor * spread, 0, 255).astype(np.uint8)
        mask_a = cv2.inRange(frame_lab[:, :, 1], int(low[1]), int(high[1]))
        mask_b = cv2.inRange(frame_lab[:, :, 2], int(low[2]), int(high[2]))
        mask = cv2.bitwise_and(mask_a, mask_b, mask=region)

        # Cleanup
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, close_kernel)
        mask = cv2.dilate(mask, final_kernel, iterations=1)
        return cv2.bitwise_and(mask, mask, mask=region)


def label_parts(mask, landmarks, geometry):
    """Gives every pixel of a binary hand mask the id of the nearest part of the
    geometric part mask. Returns (h, w) uint8: 0 background, 1 palm ... 6 pinky."""
    foreground = np.asarray(mask) > 0
    out = np.zeros(foreground.shape, np.uint8)
    if not foreground.any():
        return out

    parts = geometry.infer(foreground.shape, landmarks)
    # No usable skeleton: unknown part
    if not parts.any():
        out[foreground] = PART_IDS["palm"]
        return out

    # Crop to the hand
    ys, xs = np.nonzero(foreground | (parts > 0))
    y0 = ys.min()
    y1 = ys.max() + 1
    x0 = xs.min()
    x1 = xs.max() + 1
    parts = parts[y0:y1, x0:x1]
    foreground = foreground[y0:y1, x0:x1]

    # Each part pixel gets its own label, every other pixel the label of its nearest part pixel
    source = (parts == 0).astype(np.uint8)
    _, labels = cv2.distanceTransformWithLabels(source, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    label_to_part = np.zeros(int(labels.max()) + 1, np.uint8)
    label_to_part[labels[parts > 0]] = parts[parts > 0]
    out[y0:y1, x0:x1][foreground] = label_to_part[labels[foreground]]
    return out


class SkinSegmentation:
    """Skin segmentation per hand slot, split into parts with label_parts."""

    def __init__(self, std_factor, robust, geometry):
        self.skin = SkinHandSegmenter(std_factor, robust)
        self.geometry = geometry
        self.desc = {"seg": "skin", **self.skin.params(), "part_labels": geometry.params()}

    def __call__(self, frame, landmarks, present):
        h, w = frame.shape[:2]
        masks = np.zeros((N_SLOTS, h, w), np.uint8)
        if not present.any():
            return masks

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_lab = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2LAB)
        for slot in range(N_SLOTS):
            if present[slot]:
                skin_mask = self.skin.infer(frame_rgb, landmarks[slot], frame_lab)
                masks[slot] = label_parts(skin_mask, landmarks[slot], self.geometry)
        return masks


def load_segmentation(spec, std_factor, robust, width_scale, palm_expand, tip_extend):
    """Segmentation function from --seg: None, SkinSegmentation or a custom "module.path:function"
    with signature segment(frame_bgr, landmarks (2, 21, 3), present (2,)) -> mask."""
    if not spec or spec == "none":
        return None

    geometry = LandmarkHandSegmenter(width_scale, palm_expand, tip_extend)
    if spec == "skin":
        return SkinSegmentation(std_factor, robust, geometry)

    module_name, _, function_name = spec.partition(":")
    if not function_name:
        raise SystemExit("--seg must be 'skin', 'none' or module.path:function")
    sys.path.insert(0, str(Path.cwd()))
    function = getattr(importlib.import_module(module_name), function_name)
    function.desc = {"seg": spec}
    return function


def to_slot_parts(mask, h, w):
    """Normalizes a segmentation output to (2, h, w) uint8 part ids per slot."""
    mask = np.asarray(mask)
    if mask.shape == (N_SLOTS, h, w):
        return mask.astype(np.uint8)

    # A (h, w) mask uses 1/2 for the slot, part id 1 = whole hand
    if mask.shape == (h, w):
        mask = mask.astype(np.uint8)
        return np.stack([mask == 1, mask == 2]).astype(np.uint8)
    raise SystemExit(f"Segmentation returned {mask.shape}, expected ({N_SLOTS}, {h}, {w}) or ({h}, {w})")
