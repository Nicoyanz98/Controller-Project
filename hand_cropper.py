import os
from dataclasses import dataclass, field
from typing import Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

# Landmark indices (from the YOLO hand-pose model's keypoint layout) used to
# find "roughly where the fingers are" so the crop can be re-centered toward
# them instead of trusting the raw detection box alone.
FINGER_INDICES = {4, 8, 12, 18, 20}


@dataclass
class HandCrop:
    """One detected hand, cropped and ready for HandNetInferencer."""
    crop_rgb: np.ndarray                    # (size, size, 3) uint8 RGB
    crop_bounds: Tuple[int, int, int, int]  # (x1, y1, x2, y2) in the ORIGINAL image
    orig_box: list                          # raw YOLO box, original-image coords
    orig_kpts: np.ndarray                   # raw YOLO keypoints, original-image coords
    confidence: float
    hand_index: int                         # 1-based index among hands found in this image
    source_image: Optional[str] = None
    vector_start: Optional[Tuple[int, int]] = None  # wrist point, for debug-arrow overlay
    vector_end: Optional[Tuple[int, int]] = None    # shifted crop center, for debug-arrow overlay


class HandCropper:
    """
    Runs YOLO hand-pose detection on one image and produces expanded, keypoint-aligned square crops. The expansion + directional shift
    compensate for the raw YOLO box tending to clip fingertips / miscenter on the wrist.
    """

    def __init__(self, model_path, img_output_size=224):
        self.img_output_size = img_output_size
        self.model = YOLO(model_path)

    # Principal method
    def process(self, image_path, shift_factor=0.3, perp_shift_factor=1.0, expand_factor=1.8, save_to_disk=False, output_folder="output", save_comparison=False):
        """
        Detect + crop every hand in `image_path`. Returns list[HandCrop].

        save_to_disk=True additionally writes each crop jpg (and, if save_comparison=True, an annotated comparison image) under
        output_folder -- useful when running the cropper as standalone rather than feeding it straight into inference.
        """
        orig_img = cv2.imread(image_path)
        if orig_img is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")

        resized = cv2.resize(orig_img, (self.img_output_size, self.img_output_size), interpolation=cv2.INTER_LINEAR)
        results = self.model.predict(resized, imgsz=512, conf=0.05)

        hand_crops = self._build_crops(orig_img, results, image_path, shift_factor, perp_shift_factor, expand_factor)

        if save_to_disk:
            self._save_to_disk(hand_crops, output_folder, orig_img if save_comparison else None)

        return hand_crops

    # Detection -> crops
    def _build_crops(self, orig_img, results, image_path, shift_factor, perp_shift_factor, expand_factor):
        boxes_out = results[0].boxes
        if boxes_out is None or len(boxes_out) == 0:
            print(f"No hands detected in {image_path}.")
            return []

        orig_h, orig_w = orig_img.shape[:2]
        scale_x = orig_w / float(self.img_output_size)
        scale_y = orig_h / float(self.img_output_size)

        boxes = boxes_out.xyxy.cpu().numpy()
        confidences = boxes_out.conf.cpu().numpy()
        kpts = results[0].keypoints.xy.cpu().numpy() if results[0].keypoints is not None else None

        hand_crops = []
        for idx, (box, conf) in enumerate(zip(boxes, confidences)):
            orig_box, orig_kpts = self._scale_to_original(box, kpts, idx, scale_x, scale_y)
            crop_bgr, crop_bounds, v_start, v_end = self._crop_one_hand(orig_img, orig_box, orig_kpts, shift_factor, perp_shift_factor, expand_factor)
            crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
            hand_crops.append(HandCrop(crop_rgb, crop_bounds, orig_box, orig_kpts, float(conf), idx + 1, image_path, v_start, v_end))
        return hand_crops

    def _scale_to_original(self, box, kpts, idx, scale_x, scale_y):
        orig_box = [box[0] * scale_x, box[1] * scale_y, box[2] * scale_x, box[3] * scale_y]
        orig_kpts = (kpts[idx] * [scale_x, scale_y]) if kpts is not None and idx < len(kpts) else np.zeros((0, 2))
        return orig_box, orig_kpts

    def _crop_one_hand(self, orig_img, box, keypoints, shift_factor, perp_shift_factor, expand_factor):
        x1, y1, x2, y2 = box
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        hand_size = max(x2 - x1, y2 - y1)

        cx, cy, v_start, v_end = self._shift_center_toward_fingers(keypoints, cx, cy, shift_factor * hand_size, perp_shift_factor)

        crop_dim = hand_size * expand_factor
        crop, crop_bounds = self._extract_square_crop(orig_img, cx, cy, crop_dim)
        return crop, crop_bounds, v_start, v_end

    def _shift_center_toward_fingers(self, keypoints, cx, cy, shift_distance, perp_shift_factor):
        """
        Nudge the box center from the raw detection box towards the finger mean (compensates for YOLO boxes that hug the wrist too tightly).
        """
        v_start = (int(cx), int(cy))
        v_end = (int(cx), int(cy))

        if len(keypoints) == 0:
            return cx, cy, v_start, v_end

        wrist = keypoints[0]
        finger_pts = [pt for i, pt in enumerate(keypoints) if i in FINGER_INDICES]
        if not finger_pts:
            return cx, cy, v_start, v_end

        finger_center = np.mean(finger_pts, axis=0)
        direction = finger_center - wrist
        norm = np.linalg.norm(direction)
        if norm == 0:
            return cx, cy, v_start, v_end

        # Primary Vector (Wrist -> Finger Mean)
        ux, uy = direction / norm
        # Secondary Vector (Wrist -> Most distant finger)
        perp_ux, perp_uy, perp_dist = self._max_perpendicular_offset(wrist, finger_pts, ux, uy)

        # Shift Center
        cx += ux * shift_distance + perp_ux * perp_dist * perp_shift_factor
        cy += uy * shift_distance + perp_uy * perp_dist * perp_shift_factor

        v_start = (int(wrist[0]), int(wrist[1]))
        v_end = (int(cx), int(cy))
        return cx, cy, v_start, v_end

    @staticmethod
    def _max_perpendicular_offset(wrist, finger_pts, ux, uy):
        """
        Perpendicular axis to (wrist -> finger mean); returns the SIGNED distance of whichever finger point sits furthest
        off that axis, so the crop leans toward the side the hand actually extends into.
        """
        perp_ux, perp_uy = -uy, ux
        best_signed, best_abs = 0.0, 0.0
        for pt in finger_pts:
            v = pt - wrist
            signed = v[0] * perp_ux + v[1] * perp_uy
            if abs(signed) > best_abs:
                best_abs, best_signed = abs(signed), signed
        return perp_ux, perp_uy, best_signed

    def _extract_square_crop(self, orig_img, cx, cy, crop_dim):
        orig_h, orig_w = orig_img.shape[:2]
        # Create expanded square around the shifted center
        x1, y1 = int(cx - crop_dim / 2), int(cy - crop_dim / 2)
        x2, y2 = int(cx + crop_dim / 2), int(cy + crop_dim / 2)

        # Safe padding if out of bounds
        pad_l, pad_t = max(0, -x1), max(0, -y1)
        pad_r, pad_b = max(0, x2 - orig_w), max(0, y2 - orig_h)

        # Crop image
        region = orig_img[max(0, y1):min(orig_h, y2), max(0, x1):min(orig_w, x2)]
        if any((pad_l, pad_t, pad_r, pad_b)):
            region = cv2.copyMakeBorder(region, pad_t, pad_b, pad_l, pad_r, cv2.BORDER_CONSTANT, value=[0, 0, 0])

        crop = cv2.resize(region, (self.img_output_size, self.img_output_size), interpolation=cv2.INTER_LINEAR)
        return crop, (x1, y1, x2, y2)

    # Optional saving
    def _save_to_disk(self, hand_crops, output_folder, annotate_on=None):
        crops_dir = os.path.join(output_folder, "hand_crops")
        os.makedirs(crops_dir, exist_ok=True)

        annotated = annotate_on.copy() if annotate_on is not None else None

        for hc in hand_crops:
            path = os.path.join(crops_dir, f"hand_crop_{hc.hand_index}.jpg")
            cv2.imwrite(path, cv2.cvtColor(hc.crop_rgb, cv2.COLOR_RGB2BGR))
            print(f"Saved hand crop to '{path}'")
            if annotated is not None:
                self._draw_annotation(annotated, hc)

        if annotated is not None:
            comp_path = os.path.join(output_folder, "comparison_output.jpg")
            cv2.imwrite(comp_path, annotated)
            print(f"Saved comparison output to '{comp_path}'")

    @staticmethod
    def _draw_annotation(annotated, hc: "HandCrop"):
        # Draw Raw Prediction Box (GREEN) + Confidence
        x1, y1, x2, y2 = map(int, hc.orig_box)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(annotated, f"Hand #{hc.hand_index} ({hc.confidence:.1%})", (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Draw Final Expanded Crop Box (BLUE)
        cx1, cy1, cx2, cy2 = hc.crop_bounds
        cv2.rectangle(annotated, (cx1, cy1), (cx2, cy2), (255, 191, 0), 2)

        # Draw Keypoints (RED Dots)
        for kx, ky in hc.orig_kpts:
            if kx > 0 and ky > 0:
                cv2.circle(annotated, (int(kx), int(ky)), 4, (0, 0, 255), -1)

        # Draw Direction Vector (RED Arrow from wrist to shifted center)
        if hc.vector_start != hc.vector_end:
            cv2.arrowedLine(annotated, hc.vector_start, hc.vector_end, (0, 0, 255), 3, tipLength=0.3)


def main():
    """CLI matching the original hand_cropper.py's behavior (writes crops + comparison image to disk)."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="path to the yolo .pt file")
    parser.add_argument("--image", required=True, help="path to a single hand image")
    parser.add_argument("--image_size", type=int, default=224, help="output size for the hand crops")
    parser.add_argument("--output_folder", default="output", help="output folder name")
    args = parser.parse_args()

    cropper = HandCropper(args.model, img_output_size=args.image_size)
    cropper.process(args.image, save_to_disk=True, output_folder=args.output_folder, save_comparison=True)


if __name__ == "__main__":
    main()