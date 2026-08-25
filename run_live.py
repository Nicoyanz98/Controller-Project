import argparse
import time
import cv2
from hand_cropper import HandCropper
from inference import HandNetInferencer
from live_overlay import draw_2d_overlay
from live_visualizer import LiveHandVisualizer
from inference_worker import InferenceWorker

N_SLOTS = 2

def assign_slots(prev_centers, hand_crops):
    """
    Nearest-pair matching so a given physical hand tends to keep the same 3D panel across frames. 
    Returns (assigned_hand_crops_per_slot, updated_centers) where assigned[i] is a HandCrop or None if 
    slot i has nothing this frame.
    """
    n_slots = len(prev_centers)
    assigned = [None] * n_slots

    def center_of(hc):
        x1, y1, x2, y2 = hc.crop_bounds
        return (x1 + x2) / 2, (y1 + y2) / 2

    crop_centers = [center_of(hc) for hc in hand_crops]

    candidates = []  # (distance, slot, crop_index) for every known-slot/crop pair
    for slot in range(n_slots):
        if prev_centers[slot] is None:
            continue
        px, py = prev_centers[slot]
        for ci, (cx, cy) in enumerate(crop_centers):
            candidates.append(((cx - px) ** 2 + (cy - py) ** 2, slot, ci))
    candidates.sort(key=lambda t: t[0])

    used_slots, used_crops = set(), set()
    for _, slot, ci in candidates:
        if slot in used_slots or ci in used_crops:
            continue
        assigned[slot] = hand_crops[ci]
        used_slots.add(slot)
        used_crops.add(ci)

    # Fill any still-empty slots with leftover crops (new hands, or slots with no prior center).
    leftover = [i for i in range(len(hand_crops)) if i not in used_crops]
    for slot in range(n_slots):
        if assigned[slot] is None and leftover:
            assigned[slot] = hand_crops[leftover.pop(0)]

    new_centers = list(prev_centers)
    for slot, hc in enumerate(assigned):
        if hc is not None:
            new_centers[slot] = center_of(hc)
    return assigned, new_centers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yolo_model", required=True, help="YOLO hand-pose .pt used for cropping")
    parser.add_argument("--handnet_model", required=True, help="TorchScript-exported HandNet .pt")
    parser.add_argument("--camera", type=int, default=0, help="cv2.VideoCapture index")
    parser.add_argument("--crop_size", type=int, default=224)
    parser.add_argument("--root_index", type=int, default=9)
    parser.add_argument("--mano_pkl", default=None, help="MANO_LEFT_C.pkl / MANO_RIGHT_C.pkl for a solid mesh; omit for a point cloud")
    args = parser.parse_args()

    cropper = HandCropper(args.yolo_model, img_output_size=args.crop_size)
    inferencer = HandNetInferencer(args.handnet_model, image_size=args.crop_size, root_index=args.root_index)
    mano_faces = LiveHandVisualizer.load_mano_faces(args.mano_pkl) if args.mano_pkl else None

    live3d = LiveHandVisualizer(mano_faces=mano_faces, n_slots=N_SLOTS)
    live3d.start()

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {args.camera}")

    worker = InferenceWorker(cropper, inferencer, n_slots=N_SLOTS).start()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera read failed -- stopping.")
                break

            worker.submit_frame(frame)
            last_results, last_crop_bounds = worker.get_results()

            display = frame.copy()
            for slot in range(N_SLOTS):
                if last_results[slot] is not None:
                    draw_2d_overlay(display, last_results[slot], last_crop_bounds[slot])

            cv2.imshow("HandNet live feed", display)

            live3d.update(last_results)  # pump the 3D render/interaction loop every frame

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    finally:
        worker.stop()
        cap.release()
        cv2.destroyAllWindows()
        live3d.close()


if __name__ == "__main__":
    main()
