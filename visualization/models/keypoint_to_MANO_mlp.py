import torch.nn as nn

class KeypointsToMANOMLP(nn.Module):
    def __init__(self, input_dim=21*3, pose_dim=48, shape_dim=10):
        super(KeypointsToMANOMLP, self).__init__()

        self.features = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU()
        )

        # Parameters heads
        self.pose_head = nn.Linear(256, 48)  # 48 pose parameters for MANO
        self.shape_head = nn.Linear(256, 10)  # 10 shape parameters for MANO
        self.trans_head = nn.Linear(256, 3)  # 3 translation parameters

    def forward(self, keypoints):
        x = keypoints.view(x.size(0), -1)
        features = self.features(x)

        pose = self.pose_head(features)
        shape = self.shape_head(features)
        trans = self.trans_head(features)

        return pose, shape, trans