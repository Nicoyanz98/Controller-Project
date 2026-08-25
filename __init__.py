# Independent and lazy imports for visualization without inference
__all__ = []

try:
    from hand_cropper import HandCropper, HandCrop
    __all__ += ["HandCropper", "HandCrop"]
except ImportError:
    pass  # ultralytics/cv2 not installed

from inference_result import InferenceResult
__all__ += ["InferenceResult"]

try:
    from inference import HandNetInferencer
    __all__ += ["HandNetInferencer"]
except ImportError:
    pass  # torch not installed

from results_store import load_results, save_results
from visualizer import HandVisualizer
__all__ += ["load_results", "save_results", "HandVisualizer"]

try:
    from live_visualizer import LiveHandVisualizer
    __all__ += ["LiveHandVisualizer"]
except ImportError:
    pass  # pyvista/vtk not installed -- live 3D viewing unavailable, rest of package still works

from live_overlay import draw_2d_overlay  # cv2-only, no extra heavy deps
__all__ += ["draw_2d_overlay"]

from slot_assignment import assign_slots  # pure logic, no extra deps
__all__ += ["assign_slots"]
 
try:
    from inference_worker import InferenceWorker
    __all__ += ["InferenceWorker"]
except ImportError:
    pass