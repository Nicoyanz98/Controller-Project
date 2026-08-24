from typing import List, Optional

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import pickle

FINGER_JOINTS = {
    "thumb":  [0, 1, 2, 3, 4],
    "index":  [0, 5, 6, 7, 8],
    "middle": [0, 9, 10, 11, 12],
    "ring":   [0, 13, 14, 15, 16],
    "pinky":  [0, 17, 18, 19, 20],
}
FINGER_COLORS = {
    "thumb": "#e6194B", 
    "index": "#3cb44b", 
    "middle": "#4363d8", 
    "ring": "#f58231", 
    "pinky": "#911eb4",
}
JOINT_COLOR = {0: "black"}
for _finger, _idxs in FINGER_JOINTS.items():
    for _j in _idxs[1:]:
        JOINT_COLOR[_j] = FINGER_COLORS[_finger]


class HandVisualizer:
    """Accumulate InferenceResult objects, then build/save one interactive HTML covering all of them."""

    N_COLS = 2  # [2D panel, 3D panel] per hand -- fixed layout

    def __init__(self, mano_faces: Optional[np.ndarray] = None):
        """
        mano_faces: optional (F, 3) int array of MANO triangle indices, shared by every hand added (MANO's face 
        topology is fixed; only vertex positions vary per hand/shape).
        """
        self.mano_faces = mano_faces
        self.results = []  # list[InferenceResult], insertion order = row order

    def add_result(self, result) -> "HandVisualizer":
        self.results.append(result)
        return self

    def add_results(self, results) -> "HandVisualizer":
        for r in results:
            self.add_result(r)
        return self

    def build_figure(self) -> go.Figure:
        if not self.results:
            raise ValueError("No results added -- call add_result()/add_results() first.")

        n = len(self.results)
        fig = make_subplots(
            rows=n, cols=self.N_COLS,
            specs=[[{"type": "xy"}, {"type": "scene"}] for _ in range(n)],
            column_widths=[0.48, 0.52],
            subplot_titles=self._subplot_titles(),
            vertical_spacing=min(0.35 / n, 0.08),
        )

        trace_groups = self._add_all_panels(fig)
        ghost_traces = self._add_ghost_traces(fig)
        self._add_hand_selector(fig, trace_groups, ghost_traces)

        fig.update_layout(title="HandNet inference" + (f" ({n} hands)" if n > 1 else ""), height=max(500, 480 * n), margin=dict(l=20, r=20, t=90, b=20))
        return fig

    def save_html(self, out_path: str) -> str:
        fig = self.build_figure()
        fig.write_html(out_path, include_plotlyjs=True)
        print(f"Saved interactive visualization to {out_path} ({len(self.results)} hand(s))")
        return out_path

    @staticmethod
    def load_mano_faces(pkl_path: str) -> np.ndarray:
        """
        Load MANO triangle connectivity from a MANO_*.pkl / MANO_*_C.pkl file. 
        Expected key names: 'f' or 'faces'.
        """
        with open(pkl_path, "rb") as f:
            data = pickle.load(f, encoding="latin1")
        key = next((k for k in ("f", "faces") if k in data), None)
        if key is None:
            raise KeyError(f"No face/triangle array found in {pkl_path}. Keys: {list(data.keys())}")
        return np.array(data[key])

    def _add_ghost_traces(self, fig) -> List[int]:
        ghost_traces = []

        for finger in FINGER_JOINTS:
            fig.add_trace(
                go.Scatter(
                    x=[None], y=[None],
                    mode="lines",line=dict(color=FINGER_COLORS[finger], width=3),
                    name=finger, legendgroup=finger,
                    showlegend=True,
                ),
                row=1, col=1,
            )
            ghost_traces.append(len(fig.data) - 1)

        if self.mano_faces is not None:
            fig.add_trace(
                go.Mesh3d(
                    x=[None], y=[None], z=[None],
                    name="MANO mesh", legendgroup="mano_mesh", 
                    showlegend=True
                ),
                row=1, col=2,
            )
        else:
            fig.add_trace(
                go.Scatter3d(
                    x=[None], y=[None], z=[None],
                    name="vertices", legendgroup="vertices", 
                    showlegend=True
                ),
                row=1, col=2,
            )
        ghost_traces.append(len(fig.data) - 1)

        return ghost_traces

    def _add_all_panels(self, fig) -> List[List[int]]:
        """
        Adds every hand's 2D+3D traces to `fig`. Returns trace_groups[i] = list of trace indices belonging to
        hand i, used later to build the show-all / show-one-hand selector.
        """
        trace_groups = []
        for row, result in enumerate(self.results, start=1):
            start = len(fig.data)
            self._add_2d_panel(fig, result, row)
            self._add_3d_panel(fig, result, row)
            trace_groups.append(list(range(start, len(fig.data))))
        return trace_groups

    def _add_2d_panel(self, fig, result, row):
        img_h, img_w = result.crop_image.shape[:2]

        fig.add_layout_image(
            dict(source=self._to_pil(result.crop_image),  x=0, y=0, sizex=img_w, sizey=img_h, sizing="stretch", layer="below"),
            row=row, col=1,
        )

        uv = result.uv_pixels
        for finger, idxs in FINGER_JOINTS.items():
            fig.add_trace(
                go.Scatter(
                    x=[uv[j, 0] for j in idxs], y=[uv[j, 1] for j in idxs],
                    mode="lines", line=dict(color=FINGER_COLORS[finger], width=3),
                    name=finger, legendgroup=finger,
                    showlegend=False
                ),
                row=row, col=1,
            )

        fig.add_trace(
            go.Scatter(
                x=uv[:, 0], y=uv[:, 1], mode="markers", 
                marker=dict(size=8, color=[JOINT_COLOR[j] for j in range(21)], 
                line=dict(color="white", width=0.5)), 
                name="joints", showlegend=False
            ),
            row=row, col=1,
        )

        x_axis_name = fig.get_subplot(row, 1).xaxis.plotly_name  # e.g. "xaxis" / "xaxis2"
        fig.update_xaxes(range=[0, img_w], row=row, col=1, showgrid=False)
        fig.update_yaxes(range=[img_h, 0], row=row, col=1, showgrid=False, scaleanchor=x_axis_name.replace("axis", ""), scaleratio=1)

    def _add_3d_panel(self, fig, result, row):
        vertices, joints = result.vertices, result.joints

        if self.mano_faces is not None:
            fig.add_trace(
                go.Mesh3d(
                    x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
                    i=self.mano_faces[:, 0], j=self.mano_faces[:, 1], k=self.mano_faces[:, 2],
                    color="rgb(204,179,153)", opacity=0.55, 
                    name="MANO mesh", legendgroup="mano_mesh", 
                    showlegend=False
                ),
                row=row, col=2,
            )
        else:
            fig.add_trace(
                go.Scatter3d(
                    x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
                    mode="markers", marker=dict(size=2, color="gray", opacity=0.25),
                    name="vertices", legendgroup="vertices", 
                    showlegend=False
                ),
                row=row, col=2,
            )

        for finger, idxs in FINGER_JOINTS.items():
            fig.add_trace(
                go.Scatter3d(
                    x=joints[idxs, 0], y=joints[idxs, 1], z=joints[idxs, 2],
                    mode="lines+markers", line=dict(color=FINGER_COLORS[finger], width=6),
                    marker=dict(size=5, color=[JOINT_COLOR[j] for j in idxs], line=dict(color="black", width=0.3)),
                    name=finger, legendgroup=finger, 
                    showlegend=False
                ),
                row=row, col=2,
            )

        self._set_equal_aspect(fig, vertices, row)

    def _set_equal_aspect(self, fig, vertices, row):
        """
        Without this, the default 3D scene can stretch the hand and make it LOOK malformed even when
        the underlying prediction is fine.
        """
        max_range = np.ptp(vertices, axis=0).max() / 2.0
        mid = vertices.mean(axis=0)
        fig.update_scenes(
            xaxis=dict(range=[mid[0] - max_range, mid[0] + max_range]),
            yaxis=dict(range=[mid[1] - max_range, mid[1] + max_range]),
            zaxis=dict(range=[mid[2] - max_range, mid[2] + max_range]),
            aspectmode="cube", row=row, col=2,
        )

    def _add_hand_selector(self, fig, trace_groups: List[List[int]], ghost_traces: List[int]):
        if len(self.results) < 2:
            return  # nothing to select between with a single hand

        total = len(fig.data)
        row_axes = self._collect_row_axes(fig)

        def visibility_for(selected_rows):
            vis = [False] * total
            for i in ghost_traces:
                vis[i] = True
            for r in selected_rows:
                for i in trace_groups[r]:
                    vis[i] = True
            return vis

        buttons = [dict(
            label="All hands (together)", method="update",
            args=[{"visible": visibility_for(range(len(self.results)))}, self._row_layout(row_axes, focus_row=None)],
        )]
        for row, result in enumerate(self.results):
            buttons.append(dict(
                label=f"Hand {row + 1} only ({result.hand_id})", method="update",
                args=[{"visible": visibility_for([row])}, self._row_layout(row_axes, focus_row=row)],
            ))

        fig.update_layout(updatemenus=[dict(
            type="dropdown", direction="down", buttons=buttons,
            x=1.0, xanchor="right", y=1.12, yanchor="top", showactive=True,
        )])

    def _collect_row_axes(self, fig):
        """
        Record each row's original vertical position (yaxis + scene domains) right after make_subplots lays them out,
        so the selector can both restore them ("All hands") and expand a single row to fill the freed-up vertical
        space instead of leaving the other rows' blank space sitting there ("Hand N only").
        """
        axes = []
        for row in range(1, len(self.results) + 1):
            xy = fig.get_subplot(row, 1)
            scene = fig.get_subplot(row, 2)
            axes.append(dict(
                yaxis=xy.yaxis.plotly_name,
                yaxis_domain=list(xy.yaxis.domain),
                scene=scene.plotly_name,
                scene_domain_y=list(scene.domain.y),
            ))
        return axes

    @staticmethod
    def _row_layout(row_axes, focus_row=None):
        """
        Relayout dict for the 'update' button: 
            focus_row=None restores every row to its original height; 
            focus_row=i expands row i to (almost) the full plot height and collapses the rest to zero 
            height at their original position, so picking one hand centers/fills it vertically instead 
            of just hiding its neighbor's traces and leaving empty space behind.
        """
        relayout = {}
        if focus_row is None:
            for ax in row_axes:
                relayout[f"{ax['yaxis']}.domain"] = ax["yaxis_domain"]
                relayout[f"{ax['scene']}.domain.y"] = ax["scene_domain_y"]
            return relayout

        margin = 0.04
        for row, ax in enumerate(row_axes):
            if row == focus_row:
                relayout[f"{ax['yaxis']}.domain"] = [margin, 1 - margin]
                relayout[f"{ax['scene']}.domain.y"] = [margin, 1 - margin]
            else:
                mid = sum(ax["yaxis_domain"]) / 2.0
                relayout[f"{ax['yaxis']}.domain"] = [mid, mid]
                relayout[f"{ax['scene']}.domain.y"] = [mid, mid]
        return relayout

    def _subplot_titles(self):
        titles = []
        for r in self.results:
            titles += [f"{r.hand_id}: 2D keypoints", f"{r.hand_id}: 3D mesh"]
        return titles

    @staticmethod
    def _to_pil(arr: np.ndarray):
        return Image.fromarray(arr)