import json

import numpy as np

from hand_segmentation import PART_NAMES


class PrelabelResults:
    """Per frame results of one clip, saved as clip_XXXX_pre.npz (N frames, C zones, 2 hand slots):

        t                (N,)          s since the clip start (from the frames csv)
        labels_<group>   (N,)    str   group labels copied from the frames csv
        zone_xyxy        (N,C,4) f32   best box per YOLO class, pixels (NaN if missing)
        zone_conf        (N,C)   f32   0 if missing
        zone_valid       (N,C)   bool
        zone_mask_cov    (N,C)   f32   fraction of each zone box covered by a hand mask (NaN without --seg)
        zone_part_cov    (N,C,2,P) f32 same, per slot and hand part
        raw_boxes        (M,7)   f32   every YOLO box: frame, x1, y1, x2, y2, conf, cls
        hand_present     (N,2)   bool
        lm_img           (N,2,21,3)    filtered MediaPipe image landmarks (x, y in 0..1, z)
        lm_world         (N,2,21,3)    filtered MediaPipe world landmarks, metres, wrist centred
        lm_img_raw, lm_world_raw       same, before filtering
        hand_score       (N,2)   f32   handedness score
        handedness       (N,2)   i8    MediaPipe label: 0 Left, 1 Right, -1 none
        image_size       (2,)          width, height
        zone_names       (C,)    str   YOLO class names
        part_names       (P,)    str   hand part names (mask ids 1..P)
        meta_json        ()      str   settings used
    Masks are saved apart in clip_XXXX_masks.npz (downscaled, part ids per slot).
    """

    def __init__(self):
        self.t = []
        self.zone_xyxy = []
        self.zone_conf = []
        self.zone_coverage = []
        self.zone_part_coverage = []
        self.raw_boxes = []
        self.hand_present = []
        self.landmarks_img = []
        self.landmarks_world = []
        self.landmarks_img_raw = []
        self.landmarks_world_raw = []
        self.hand_score = []
        self.handedness = []
        self.masks = []

    def __len__(self):
        return len(self.t)

    def add_frame(self, t, zones, hands, raw_boxes):
        """zones: (xyxy, conf, coverage, part_coverage), hands: FrameHands of the frame."""
        xyxy, conf, coverage, part_coverage = zones
        self.t.append(t)
        self.zone_xyxy.append(xyxy)
        self.zone_conf.append(conf)
        self.zone_coverage.append(coverage)
        self.zone_part_coverage.append(part_coverage)
        if len(raw_boxes):
            self.raw_boxes.append(raw_boxes)

        self.hand_present.append(hands.present)
        self.landmarks_img.append(hands.landmarks_img)
        self.landmarks_world.append(hands.landmarks_world)
        self.landmarks_img_raw.append(hands.landmarks_img_raw)
        self.landmarks_world_raw.append(hands.landmarks_world_raw)
        self.hand_score.append(hands.score)
        self.handedness.append(hands.handedness)

    def add_masks(self, masks):
        self.masks.append(masks)

    def save(self, path, image_size, zone_names, labels, meta):
        """labels: {group: list of per frame labels}."""
        if self.raw_boxes:
            raw_boxes = np.concatenate(self.raw_boxes)
        else:
            raw_boxes = np.zeros((0, 7), np.float32)

        label_arrays = {}
        for group, group_labels in labels.items():
            label_arrays[f"labels_{group}"] = np.array(group_labels)

        zone_conf = np.stack(self.zone_conf)
        np.savez_compressed(
            path,
            t=np.array(self.t, np.float32),
            zone_xyxy=np.stack(self.zone_xyxy),
            zone_conf=zone_conf,
            zone_valid=zone_conf > 0,
            zone_mask_cov=np.stack(self.zone_coverage),
            zone_part_cov=np.stack(self.zone_part_coverage),
            raw_boxes=raw_boxes,
            hand_present=np.stack(self.hand_present),
            lm_img=np.stack(self.landmarks_img),
            lm_world=np.stack(self.landmarks_world),
            lm_img_raw=np.stack(self.landmarks_img_raw),
            lm_world_raw=np.stack(self.landmarks_world_raw),
            hand_score=np.stack(self.hand_score),
            handedness=np.stack(self.handedness),
            image_size=np.array(image_size, np.int32),
            zone_names=np.array(zone_names),
            part_names=np.array(PART_NAMES),
            meta_json=np.array(json.dumps(meta)),
            **label_arrays,
        )

    def save_masks(self, path):
        if self.masks:
            np.savez_compressed(path, masks=np.stack(self.masks), part_names=np.array(PART_NAMES))

    def stats(self, zone_names):
        """Hand and zone detection rates of the clip, for prelabel_summary.csv."""
        present = np.stack(self.hand_present)
        zone_valid = np.stack(self.zone_conf) > 0
        stats = {
            "hand0_rate": round(float(present[:, 0].mean()), 3),
            "hand1_rate": round(float(present[:, 1].mean()), 3),
            "both_hands_rate": round(float(present.all(1).mean()), 3),
        }
        for cls, name in enumerate(zone_names):
            stats[f"zone_{name}_rate"] = round(float(zone_valid[:, cls].mean()), 3)
        return stats
