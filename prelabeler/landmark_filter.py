import math

import numpy as np


def _alpha(t_e, cutoff):
    r = 2 * math.pi * cutoff * t_e
    return r / (r + 1)


class OneEuroFilter:
    """Element-wise One Euro filter (Casiez et al. 2012) over an array of any shape.

    A (21, 3) array behaves like 21 independent landmark filters over x, y, z.
        min_cutoff  increase if laggy, decrease if jittery at rest
        beta        increase to reduce lag during fast movements
    """

    def __init__(self, t0, x0, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)

        self.x_prev = np.array(x0, dtype=np.float64)
        self.dx_prev = np.zeros_like(self.x_prev)
        self.t_prev = float(t0)

    def __call__(self, t, x):
        x = np.asarray(x, dtype=np.float64)
        t_e = float(t) - self.t_prev
        # Duplicate or out of order timestamp
        if t_e <= 0:
            return self.x_prev.copy()

        # Smoothed speed
        a_d = _alpha(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = a_d * dx + (1 - a_d) * self.dx_prev

        # Faster movement -> higher cutoff -> less lag
        cutoff = self.min_cutoff + self.beta * np.abs(dx_hat)
        a = _alpha(t_e, cutoff)
        x_hat = a * x + (1 - a) * self.x_prev

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = float(t)
        return x_hat.copy()


class LandmarkFilterBank:
    """One OneEuroFilter per hand slot. A hand that appears starts a fresh filter at its
    current pose, a hand missing in a frame loses its filter (call keep_only after each frame).

    max_jump: if the wrist moves more than this (normalized units) between frames the
    filter restarts instead of smoothing, guards against two hands swapping slots.
    """

    def __init__(self, min_cutoff=2.5, beta=1.5, d_cutoff=1.0, enabled=True, max_jump=None):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.enabled = enabled
        self.max_jump = max_jump

        self.filters = {}

    def apply(self, slot, landmarks, t):
        """Returns the filtered copy of the (21, D) landmarks of a slot."""
        landmarks = np.asarray(landmarks, dtype=np.float64)
        if not self.enabled or not np.isfinite(landmarks).all():
            return landmarks.astype(np.float32)

        if self.max_jump is not None and slot in self.filters:
            wrist_jump = np.linalg.norm(landmarks[0, :2] - self.filters[slot].x_prev[0, :2])
            if wrist_jump > self.max_jump:
                del self.filters[slot]

        if slot not in self.filters:
            self.filters[slot] = OneEuroFilter(t, landmarks, self.min_cutoff, self.beta, self.d_cutoff)
            return landmarks.astype(np.float32)
        return self.filters[slot](t, landmarks).astype(np.float32)

    def keep_only(self, slots):
        """Drops the filters of the slots without a hand."""
        for slot in list(self.filters):
            if slot not in slots:
                del self.filters[slot]

    def params(self):
        return {
            "min_cutoff": self.min_cutoff,
            "beta": self.beta,
            "d_cutoff": self.d_cutoff,
            "enabled": self.enabled,
            "max_jump": self.max_jump,
        }
