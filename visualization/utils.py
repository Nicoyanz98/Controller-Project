import threading
import copy

class HandDataMutex:
    def __init__(self):
        self.lock = threading.Lock()
        self.detection = {}
        self.exists = False

    def save_result(self, handedness, data):
        with self.lock:
            self.detection[handedness] = data

    def clear(self, keep=[]):
        with self.lock:
            self.detection = {key: self.detection[key] for key in keep if key in self.detection}

    def get_result(self):
        with self.lock:
            return dict(self.detection) if self.detection is not None else {}

class BoxesMutex:
    def __init__(self):
        self.lock = threading.Lock()
        self.detection = None

    def save_results(self, result):
        with self.lock:
            self.detection = None
            self.detection = result

    def clear(self):
        with self.lock:
            self.detection = None

    def get_result(self):
        with self.lock:
            return copy.deepcopy(self.detection)

import numpy as np

# Credit to https://github.com/jaantollander/OneEuroFilter
class OneEuroFilter: 
    def __init__(self, t0, x0, dx0=0.0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev = np.array(x0, dtype=float)
        self.dx_prev = np.array(dx0, dtype=float)
        self.t_prev = float(t0)

    def _alpha(self, cutoff, dt):
        tau = 1.0 / (2 * np.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, t, x):
        t = float(t)
        x = np.array(x, dtype=float)
        dt = t - self.t_prev
        
        # Prevent division by zero if frames arrive at the exact same millisecond
        if dt <= 0:
            return self.x_prev

        # Filter the derivative (velocity) to handle jitter
        a_d = self._alpha(self.d_cutoff, dt)
        dx = (x - self.x_prev) / dt
        dx_hat = a_d * dx + (1.0 - a_d) * self.dx_prev

        # Update cutoff frequency based on velocity
        cutoff = self.min_cutoff + self.beta * np.abs(dx_hat)

        # Filter the actual position
        a = self._alpha(cutoff, dt)
        x_hat = a * x + (1.0 - a) * self.x_prev

        # Save current state for the next frame
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t

        return x_hat
