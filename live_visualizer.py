from typing import Dict, List, Optional, Tuple

import numpy as np
import pyvista as pv
import pickle

from inference import InferenceResult

FINGER_JOINTS = {
    "thumb":  [0, 1, 2, 3, 4],
    "index":  [0, 5, 6, 7, 8],
    "middle": [0, 9, 10, 11, 12],
    "ring":   [0, 13, 14, 15, 16],
    "pinky":  [0, 17, 18, 19, 20],
}
FINGER_COLORS = {
    "thumb": "#e6194B", "index": "#3cb44b", "middle": "#4363d8",
    "ring": "#f58231", "pinky": "#911eb4",
}


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


JOINT_RGB = {0: (0, 0, 0)}
for _finger, _idxs in FINGER_JOINTS.items():
    for _j in _idxs[1:]:
        JOINT_RGB[_j] = _hex_to_rgb(FINGER_COLORS[_finger])


class _SlotActors:
    """
    Everything drawn in one sub-viewport: the mesh/point-cloud plus 5 finger-line actors plus one joint-marker actor.
    Created once per slot, then only had their PolyData `.points` mutated afterward.
    """

    def __init__(self):
        self.mesh_poly: Optional[pv.PolyData] = None
        self.finger_polys: Dict[str, pv.PolyData] = {}
        self.joint_poly: Optional[pv.PolyData] = None
        self.last_result: Optional[InferenceResult] = None  # identity check to skip no-op updates

    @property
    def is_created(self) -> bool:
        return self.mesh_poly is not None


class LiveHandVisualizer:
    """
    Single PyVista render window with `n_slots` side-by-side viewports; feed it the latest InferenceResult per slot 
    every video frame via update().
    """

    def __init__(self, mano_faces: Optional[np.ndarray] = None, n_slots: int = 2, window_size=(1200, 600), off_screen: bool = False):
        self.mano_faces = mano_faces
        self._pv_faces = self._to_pv_faces(mano_faces) if mano_faces is not None else None
        self.n_slots = n_slots
        self.plotter = pv.Plotter(shape=(1, n_slots), window_size=window_size, title="HandNet live 3D", off_screen=off_screen)
        self.plotter.set_background("white")
        self.slots = [_SlotActors() for _ in range(n_slots)]
        self._started = False

    def start(self):
        """Open the render window without blocking. Call once before the first update() in the live loop."""
        for i in range(self.n_slots):
            self.plotter.subplot(0, i)
            self.plotter.add_text(f"Hand slot {i + 1}: waiting...", font_size=10, name=f"label{i}")
        self.plotter.show(interactive_update=True, auto_close=False)
        self._started = True

    def update(self, results_per_slot: List[Optional[InferenceResult]]):
        """
        results_per_slot[i]: the InferenceResult currently assigned to slot i, or None to leave that slot's last 
        drawing untouched. 
        """
        if not self._started:
            self.start()

        for i, result in enumerate(results_per_slot[: self.n_slots]):
            if result is None or result is self.slots[i].last_result:
                continue
            self.plotter.subplot(0, i)
            self._update_slot(self.slots[i], result, i)

        self.plotter.update()

    def close(self):
        self.plotter.close()

    @staticmethod
    def load_mano_faces(pkl_path: str) -> np.ndarray:
        with open(pkl_path, "rb") as f:
            data = pickle.load(f, encoding="latin1")
        key = next((k for k in ("f", "faces") if k in data), None)
        if key is None:
            raise KeyError(f"No face/triangle array found in {pkl_path}. Keys: {list(data.keys())}")
        return np.array(data[key])

    def _update_slot(self, slot: _SlotActors, result: InferenceResult, slot_idx: int):
        if not slot.is_created:
            self._create_slot_actors(slot, result, slot_idx)
        else:
            slot.mesh_poly.points = result.vertices
            for finger, poly in slot.finger_polys.items():
                poly.points = result.joints[FINGER_JOINTS[finger]]
            slot.joint_poly.points = result.joints

        slot.last_result = result
        self.plotter.add_text(f"Hand slot {slot_idx + 1}: {result.hand_id}", font_size=10, name=f"label{slot_idx}")

    def _create_slot_actors(self, slot: _SlotActors, result: InferenceResult, slot_idx: int):
        if self._pv_faces is not None:
            slot.mesh_poly = pv.PolyData(result.vertices, self._pv_faces)
            self.plotter.add_mesh(slot.mesh_poly, color="#ccb399", opacity=0.55, name=f"mesh{slot_idx}")
        else:
            slot.mesh_poly = pv.PolyData(result.vertices)
            self.plotter.add_mesh(slot.mesh_poly, color="gray", opacity=0.3, point_size=3, render_points_as_spheres=True, name=f"mesh{slot_idx}")

        for finger, idxs in FINGER_JOINTS.items():
            poly = pv.PolyData(result.joints[idxs])
            poly.lines = np.hstack([[len(idxs)], np.arange(len(idxs))])
            self.plotter.add_mesh(poly, color=FINGER_COLORS[finger], line_width=6, name=f"finger{slot_idx}_{finger}")
            slot.finger_polys[finger] = poly

        slot.joint_poly = pv.PolyData(result.joints)
        slot.joint_poly["colors"] = np.array(
            [JOINT_RGB[j] for j in range(len(result.joints))], dtype=np.uint8)
        self.plotter.add_mesh(slot.joint_poly, scalars="colors", rgb=True, point_size=10, render_points_as_spheres=True, name=f"joints{slot_idx}")

        self.plotter.reset_camera()  # only on first-ever data for this slot

    @staticmethod
    def _to_pv_faces(mano_faces: np.ndarray) -> np.ndarray:
        """
        PyVista's PolyData face array needs each triangle prefixed with its vertex count: [3, i, j, k, 3, i, j, k, ...].
        """
        n = mano_faces.shape[0]
        return np.hstack([np.full((n, 1), 3), mano_faces]).astype(np.int64).flatten()
