from torch.utils.data import Dataset, DataLoader
import os
import json
import torch
import torch.nn as nn
from config import CONFIG
import numpy as np

from keypoint_to_mesh import KeypointToMesh

class InterHand26MDataset(Dataset):
    def __init__(self, data_root, split='train'):
        """
        data_root directory structure:
        ├── annotations/
        │   └── {split}/
        │       ├── InterHand2.6M_{split}_data.json
        │       ├── InterHand2.6M_{split}_joint_3d.json
        │       └── InterHand2.6M_{split}_MANO_NeuralAnnot.json
        """
        self.data_root = data_root
        annot_dir = os.path.join(data_root, 'annotations', split)

        data_path = os.path.join(annot_dir, f'InterHand2.6M_{split}_data.json')
        joint_path = os.path.join(annot_dir, f'InterHand2.6M_{split}_joint_3d.json')
        mano_path = os.path.join(annot_dir, f'InterHand2.6M_{split}_MANO_NeuralAnnot.json')

        print("Loading InterHand2.6M JSON annotations...")
        with open(data_path, 'r') as f:
            self.data_info = json.load(f)
        with open(joint_path, 'r') as f:
            self.joint_3d_info = json.load(f)
        with open(mano_path, 'r') as f:
            self.mano_info = json.load(f)

        print("Indexing right-hand annotations...")
        self.samples = []

        # InterHand2.6M_data.json: 'annotations' is a LIST of image annotations
        for annot in self.data_info['annotations']:
            # Filter for valid single right hand annotations
            if annot['hand_type'] == 'right' and annot['hand_type_valid'] == 1:
                image_id = annot['image_id']
                img_info = self.data_info['images'][image_id]

                capture_id = str(img_info['capture'])
                frame_idx = str(img_info['frame_idx'])

                # Verify MANO annotations exist for this capture and frame
                if capture_id in self.mano_info and frame_idx in self.mano_info[capture_id]:
                    mano_frame = self.mano_info[capture_id][frame_idx]
                    
                    if 'right' in mano_frame and mano_frame['right'] is not None:
                        self.samples.append({
                            'capture_id': capture_id,
                            'frame_idx': frame_idx,
                            'mano': mano_frame['right']
                        })

        print(f"Dataset initialized with {len(self.samples)} valid right-hand frames.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        capture_id = sample['capture_id']
        frame_idx = sample['frame_idx']

        # 1. Load 3D Joints from world_coord (mm)
        # InterHand joint structure: 42 joints total -> [0:21] Left Hand, [21:42] Right Hand
        joint_data = self.joint_3d_info[capture_id][frame_idx]
        world_joints = np.array(joint_data['world_coord'], dtype=np.float32)  # (42, 3)
        right_joints = world_joints[21:42]  # Extract 21 right hand joints (mm)

        # Convert to meters
        right_joints = right_joints / 1000.0

        # 2. Extract MANO Ground Truth Annotations
        mano_pose = np.array(sample['mano']['pose'], dtype=np.float32)   # (48,)
        mano_shape = np.array(sample['mano']['shape'], dtype=np.float32) # (10,)
        mano_trans = np.array(sample['mano']['trans'], dtype=np.float32) # (3,) meters

        # 3. Center Keypoints around Wrist (Joint Index 0)
        wrist = right_joints[0:1, :]
        normalized_joints = right_joints - wrist

        return {
            'input_keypoints': torch.tensor(normalized_joints, dtype=torch.float32), # (21, 3)
            'gt_joints': torch.tensor(normalized_joints, dtype=torch.float32),        # (21, 3)
            'gt_pose': torch.tensor(mano_pose, dtype=torch.float32),                  # (48,)
            'gt_shape': torch.tensor(mano_shape, dtype=torch.float32),                # (10,)
            'gt_trans': torch.tensor(mano_trans, dtype=torch.float32)                 # (3,)
        }

def train():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on device: {device}")
    
    # Hyperparameters
    BATCH_SIZE = CONFIG['TRAIN']['BATCH_SIZE']
    EPOCHS = CONFIG['TRAIN']['EPOCHS']
    LR = CONFIG['TRAIN']['LEARNING_RATE']
    DATA_ROOT = CONFIG['TRAIN']['DATA_ROOT']
    MANO_PATH = CONFIG['MANO']['path']

    # Datasets and Loaders
    train_dataset = InterHand26MDataset(data_root=DATA_ROOT, split='train')
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)

    model = KeypointToMesh(mano_root=MANO_PATH).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0
        
        for batch_idx, batch in enumerate(train_loader):
            input_kps = batch['input_keypoints'].to(device)
            gt_joints = batch['gt_joints'].to(device)
            gt_pose = batch['gt_pose'].to(device)
            gt_shape = batch['gt_shape'].to(device)

            optimizer.zero_grad()
            
            # Forward Pass through MLP + MANO Layer
            pred_verts, pred_joints, pred_pose, pred_shape = model(input_kps)
            
            # Loss Functions
            loss_3d_joints = nn.functional.mse_loss(pred_joints, gt_joints)
            loss_pose = nn.functional.mse_loss(pred_pose, gt_pose)
            loss_shape = nn.functional.mse_loss(pred_shape, gt_shape)
            
            # Regularizations to keep angles/shapes in valid bounds
            reg_pose = torch.mean(pred_pose ** 2)
            reg_shape = torch.mean(pred_shape ** 2)
            
            # Combined Loss Function
            loss = loss_3d_joints + (0.1 * loss_pose) + (0.01 * loss_shape) + (0.001 * reg_pose) + (0.001 * reg_shape)
            
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            
            if batch_idx % 100 == 0:
                print(f"Epoch [{epoch+1}/{EPOCHS}] | Batch [{batch_idx}/{len(train_loader)}] | Loss: {loss.item():.6f}")
        
        scheduler.step()
        print(f"--- Epoch {epoch+1} Complete | Avg Loss: {running_loss/len(train_loader):.6f} ---")
        
        # Save Checkpoint
        os.makedirs("checkpoints", exist_ok=True)
        torch.save(model.state_dict(), f"checkpoints/mano_mlp_epoch_{epoch+1}.pth")

if __name__ == "__main__":
    train()