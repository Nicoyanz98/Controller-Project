"""
Shared result type. Split out from inference.py so that loading/viewing an
already-built results store (results_store.py + visualizer.py) never
requires torch to be installed -- only actually running the model
(inference.py -> HandNetInferencer) does.
"""
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np


@dataclass
class InferenceResult:
    """Inference result to redraw one hand's 2D+3D visualization later, without re-running the model."""
    hand_id: str                         # unique key, e.g. "photo01_hand2"
    uv_pixels: np.ndarray                # (21, 2) in crop pixel space
    joints: np.ndarray                   # (21, 3) root-centered
    vertices: np.ndarray                 # (778, 3) root-centered
    crop_image: np.ndarray               # (H, W, 3) uint8 RGB -- exact crop fed to the model
    source_image: Optional[str] = None   # original full-image path, if any
    crop_bounds: Optional[tuple] = None  # (x1, y1, x2, y2) in the source image, if any
    root_index: int = 9
    model_path: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)
