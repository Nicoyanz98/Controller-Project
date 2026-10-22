import numpy as np

from hand_slots import N_SLOTS
from hand_segmentation import N_PARTS


def best_per_class(detections, n_classes):
    """Highest confidence box of every zone class. Missing classes get NaN boxes and conf 0."""
    xyxy = np.full((n_classes, 4), np.nan, np.float32)
    conf = np.zeros(n_classes, np.float32)
    for x1, y1, x2, y2, box_conf, cls in detections:
        cls = int(cls)
        if 0 <= cls < n_classes and box_conf > conf[cls]:
            xyxy[cls] = (x1, y1, x2, y2)
            conf[cls] = box_conf
    return xyxy, conf


def zone_coverage(masks, xyxy, valid):
    """Fraction of each zone box covered by any hand (C,) and by each slot part (C, 2, P)."""
    _, h, w = masks.shape
    n_classes = len(xyxy)
    any_coverage = np.full(n_classes, np.nan, np.float32)
    part_coverage = np.full((n_classes, N_SLOTS, N_PARTS), np.nan, np.float32)

    for cls in np.flatnonzero(valid):
        x1, y1, x2, y2 = xyxy[cls]
        x1 = max(int(np.floor(x1)), 0)
        y1 = max(int(np.floor(y1)), 0)
        x2 = min(int(np.ceil(x2)), w)
        y2 = min(int(np.ceil(y2)), h)
        if x2 <= x1 or y2 <= y1:
            any_coverage[cls] = 0.0
            part_coverage[cls] = 0.0
            continue

        crop = masks[:, y1:y2, x1:x2]
        area = crop.shape[1] * crop.shape[2]
        any_coverage[cls] = (crop > 0).any(0).mean()
        for slot in range(N_SLOTS):
            part_counts = np.bincount(crop[slot].ravel(), minlength=N_PARTS + 1)
            part_coverage[cls, slot] = part_counts[1:N_PARTS + 1] / area
    return any_coverage, part_coverage
