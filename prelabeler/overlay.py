import cv2
import numpy as np

from hand_slots import WRIST, N_SLOTS

SLOT_COLORS = [(255, 120, 0), (0, 220, 0)]
PART_COLORS = [(0, 0, 0), (200, 200, 200), (0, 0, 255), (0, 165, 255), (0, 255, 255), (0, 255, 0), (255, 0, 0)]
ZONE_COLOR = (0, 200, 255)


class OverlayWriter:
    """Writes clip_XXXX_overlay.mp4 with the zones, hand landmarks, masks and group labels, for visual QA."""

    def __init__(self, path, fps):
        self.path = path
        self.fps = fps
        self.writer = None

    def write(self, frame, xyxy, conf, zone_names, landmarks, present, masks, labels):
        image = frame.copy()
        h, w = image.shape[:2]
        if self.writer is None:
            self.writer = cv2.VideoWriter(str(self.path), cv2.VideoWriter_fourcc(*"mp4v"), self.fps, (w, h))

        if masks is not None:
            for slot in range(N_SLOTS):
                _draw_parts(image, masks[slot])

        for cls in np.flatnonzero(conf > 0):
            x1, y1, x2, y2 = xyxy[cls].astype(int)
            cv2.rectangle(image, (x1, y1), (x2, y2), ZONE_COLOR, 2)
            cv2.putText(image, f"{zone_names[cls]} {conf[cls]:.2f}", (x1, max(y1 - 5, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, ZONE_COLOR, 1)

        for slot in range(N_SLOTS):
            if not present[slot]:
                continue
            for x, y, _ in landmarks[slot]:
                cv2.circle(image, (int(x * w), int(y * h)), 3, SLOT_COLORS[slot], -1)
            x, y = landmarks[slot][WRIST, :2]
            cv2.putText(image, f"slot{slot}", (int(x * w), int(y * h) + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, SLOT_COLORS[slot], 2)

        text = "  ".join(f"{group}:{label}" for group, label in labels.items())
        cv2.putText(image, text, (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        self.writer.write(image)

    def close(self):
        if self.writer is not None:
            self.writer.release()


def _draw_parts(image, mask, alpha=0.45):
    """Blends a part id mask onto the image, one color per part."""
    selected = mask > 0
    if not selected.any():
        return
    colors = np.array(PART_COLORS, np.uint8)[mask[selected]]
    image[selected] = (image[selected] * (1 - alpha) + colors * alpha).astype(np.uint8)
