from typing import Optional, List

import numpy as np
import torch
from PIL import Image

from inference_result import InferenceResult


class HandNetInferencer:
    """Wraps a TorchScript HandNet model: preprocessing, forward pass, and root-centering"""

    def __init__(self, model_path, image_size=224, root_index=0, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.image_size = image_size
        self.root_index = root_index
        self.model_path = model_path
        self.model = torch.jit.load(model_path, map_location=self.device)
        self.model.eval()

    def infer_one(self, crop_rgb: np.ndarray, hand_id: str, source_image: Optional[str] = None, crop_bounds: Optional[tuple] = None) -> InferenceResult:
        """Run inference on a single in-memory RGB crop."""
        return self.infer_batch([crop_rgb], [hand_id], source_images=[source_image], crop_bounds_list=[crop_bounds])[0]

    def infer_batch(self, crops_rgb: List[np.ndarray], hand_ids: List[str], source_images: Optional[List[str]] = None, crop_bounds_list: Optional[List[tuple]] = None) -> List[InferenceResult]:
        """Run inference on a list of in-memory RGB crops in a single forward pass."""
        n = len(crops_rgb)
        source_images = source_images or [None] * n
        crop_bounds_list = crop_bounds_list or [None] * n

        batch_tensor = torch.cat([self._preprocess(c) for c in crops_rgb], dim=0)
        uv, joints, vertices = self._forward(batch_tensor)
        joints, vertices = self._root_center(joints, vertices)

        uv = uv.cpu().numpy()
        joints = joints.cpu().numpy()
        vertices = vertices.cpu().numpy()

        return [
            InferenceResult(
                hand_id=hand_ids[i],
                uv_pixels=uv[i] * self.image_size,
                joints=joints[i],
                vertices=vertices[i],
                crop_image=crops_rgb[i],
                source_image=source_images[i],
                crop_bounds=crop_bounds_list[i],
                root_index=self.root_index,
                model_path=self.model_path,
            )
            for i in range(n)
        ]

    def _preprocess(self, crop_rgb: np.ndarray) -> torch.Tensor:
        """
        Resize a single HxWx3 RGB uint8 crop to the model's input size and turn it into a (1, 3, size, size) float tensor of RAW 0-255 pixel
        values. Normalization is not necessary because HandNet already normalizes the image.
        """
        img = Image.fromarray(crop_rgb).resize((self.image_size, self.image_size))
        arr = np.array(img).astype(np.float32)
        return torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)

    def _forward(self, batch_tensor: torch.Tensor):
        with torch.no_grad():
            res = self.model(batch_tensor.to(self.device).float())
        vertices = res["vertices"].reshape(-1, 778, 3)
        joints = res["joints"].reshape(-1, 21, 3)
        uv = res["uv"].reshape(-1, 21, 2)
        return uv, joints, vertices

    def _root_center(self, joints, vertices):
        """Re-express joints/vertices relative to `root_index` (the network's raw 3D output has no meaningful absolute position)."""
        root = joints[:, self.root_index][:, None, :]
        return joints - root, vertices - root
