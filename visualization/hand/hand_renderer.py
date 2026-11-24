import numpy as np
import pyvista as pv
from functools import wraps

class Hand3DRenderer:
    def __init__(self, hand_lines):
        self.plotter = pv.Plotter()
        self.plotter.show_axes()
        self.plotter.show_bounds(grid=True, location='outer', all_edges=True, color='white', font_size=10)
        self.plotter.set_background('black')

        self.plotter.camera.parallel_projection = False
        self.plotter.camera_position = [
            (0.5, -0.5, 3.0),  # Camera location in 3D (X, Y, Z)
            (0.5, -0.5, 0.0),  # Focal point (where the camera is looking)
            (0.0, 1.0, 0.0)    # "Up" vector (Y-axis points up)
        ]
        
        self.hand_colors = {'Left': 'cyan', 'Right': 'magenta'}
        self.hand_meshes = {}

        self.start()
        
        self._initialize_hand_meshes(hand_lines)

    def _initialize_hand_meshes(self, hand_lines):
        dummy_points = np.zeros((21, 3), dtype=np.float32)
        for side, color in self.hand_colors.items():
            self._update_hand(dummy_points, side, color, hand_lines=hand_lines, new=True)
        self._hide_hands()

    def start(self):
        self.running = True
        self.plotter.show(interactive_update=True, auto_close=False)

    def if_plotter_is_running(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.running:
                return
            return func(self, *args, **kwargs)
        return wrapper

    @if_plotter_is_running
    def _update_hand(self, pts, side, color, hand_lines=None, new=False):
        if not new and side not in self.hand_meshes:
            print(f"Warning: Unknown hand side '{side}'")
            return
        
        if new:
            mesh = pv.PolyData(pts.copy(), lines=hand_lines)
        else:
            mesh = self.hand_meshes[side]
            mesh.points = pts.copy()

        vert_cells = np.array([item for i in range(len(pts)) for item in [1, i]])
        mesh.verts = vert_cells
        self.hand_meshes[side] = mesh

        self.plotter.add_mesh(
            mesh,
            color=color, 
            point_size=13,
            line_width=3, 
            render_points_as_spheres=True, 
            name=f"hand_points_{side}",
            reset_camera=False
        )

    @if_plotter_is_running
    def _hide_hands(self, keep=[]):
        for side in self.hand_colors.keys():
            if side not in keep:
                self.plotter.remove_actor(f"hand_points_{side}", reset_camera=False)

    @if_plotter_is_running
    def render_hands(self, sides, pts_arr):
        for side, pts in zip(sides, pts_arr):
            self._update_hand(pts, side, self.hand_colors.get(side, 'green'))

        self._hide_hands(keep=sides)

        self.plotter.update(1)

    @if_plotter_is_running
    def close(self):
        self.running = False
        self.plotter.close()
        self.plotter = None