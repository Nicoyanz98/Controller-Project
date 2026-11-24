import torch
import torch.nn as nn
from manopth.manolayer import ManoLayer
from .keypoint_to_MANO_mlp import KeypointsToMANOMLP

class KeypointToMesh(nn.Module):
    def __init__(self, mano_model_path="models/mano", is_rhand=True):
        super().__init__()
        
        # 1. MLP Network
        self.mlp = KeypointsToMANOMLP(num_keypoints=21, pose_dim=48, shape_dim=10)
        
        # 2. Differentiable MANO Layer
        # pose_dim=48 includes 3 global rotation params + 45 pose params (15 joints * 3)
        self.mano_layer = ManoLayer(
            mano_root=mano_model_path,
            side='right' if is_rhand else 'left',
            use_pca=False,         # Use raw axis-angle (15x3) instead of PCA components
            flat_hand_mean=True    # Zero-centered rest pose setup
        )

    def forward(self, input_keypoints):
        """
        Input:
            input_keypoints: Tensor of shape (Batch, 21, 3)
        Output:
            vertices: Tensor of shape (Batch, 778, 3) - 3D mesh vertices
            joints: Tensor of shape (Batch, 21, 3) - Regressed 3D joint locations
        """
        # Step A: Predict MANO parameters
        pose, shape, trans = self.mlp(input_keypoints)
        
        # # Separate global rotation (first 3) from finger pose parameters (45)
        # global_rot = pose[:, :3]
        # hand_pose = pose[:, 3:]

        # Step B: Pass through Differentiable MANO Layer
        # MANO outputs vertices (778 nodes) and joint positions (21 nodes)
        vertices, joints = self.mano_layer(th_pose_coeffs=torch.cat([global_rot, hand_pose], dim=1), th_betas=shape)
        
        # Step C: Apply global translation
        vertices = (vertices / 1000.0) + trans.unsqueeze(1)
        joints = (joints / 1000.0) + trans.unsqueeze(1)

        return vertices, joints