import cv2
import numpy as np

FINGER_JOINTS = {
    "thumb":  [0, 1, 2, 3, 4],
    "index":  [0, 5, 6, 7, 8],
    "middle": [0, 9, 10, 11, 12],
    "ring":   [0, 13, 14, 15, 16],
    "pinky":  [0, 17, 18, 19, 20],
}
# BGR (not RGB) since these get drawn straight into an OpenCV frame.
FINGER_BGR = {
    "thumb": (75, 25, 230), "index": (60, 180, 75), "middle": (216, 99, 67),
    "ring": (49, 130, 245), "pinky": (180, 30, 145),
}


def draw_2d_overlay(frame_bgr: np.ndarray, result, crop_bounds) -> np.ndarray:
    """
    Draw `result.uv_pixels` (in CROP pixel space, per HandNetInferencer's image_size) onto `frame_bgr`, remapped into 
    the region `crop_bounds` = (x1, y1, x2, y2) occupies in the frame. 
    Mutates and returns `frame_bgr`.
    """
    x1, y1, x2, y2 = crop_bounds
    crop_w, crop_h = max(x2 - x1, 1), max(y2 - y1, 1)
    crop_img_h, crop_img_w = result.crop_image.shape[:2]
    scale_x = crop_w / crop_img_w
    scale_y = crop_h / crop_img_h

    def to_frame(pt):
        return int(x1 + pt[0] * scale_x), int(y1 + pt[1] * scale_y)

    uv = result.uv_pixels
    for finger, idxs in FINGER_JOINTS.items():
        pts = [to_frame(uv[j]) for j in idxs]
        color = FINGER_BGR[finger]
        for a, b in zip(pts, pts[1:]):
            cv2.line(frame_bgr, a, b, color, 2, cv2.LINE_AA)
        for p in pts:
            cv2.circle(frame_bgr, p, 4, color, -1, cv2.LINE_AA)

    cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (255, 191, 0), 1)
    return frame_bgr
