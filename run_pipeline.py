import argparse
import os

from hand_cropper import HandCropper
from inference import HandNetInferencer
from results_store import save_results
from visualizer import HandVisualizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yolo_model", required=True, help="YOLO hand-pose .pt used for cropping")
    parser.add_argument("--handnet_model", required=True, help="TorchScript-exported HandNet .pt")
    parser.add_argument("--image", required=True, help="path to one photo (may contain multiple hands)")
    parser.add_argument("--crop_size", type=int, default=224, help="must match the size HandNet was exported/trained with")
    parser.add_argument("--root_index", type=int, default=9, help="cfg.py DATA.ROOT_INDEX=9 vs VAL.ROOT_INDEX=0 -- unresolved, try both")
    parser.add_argument("--mano_pkl", default=None, help="MANO_LEFT_C.pkl / MANO_RIGHT_C.pkl for a solid mesh; omit for a point cloud")
    parser.add_argument("--results", default="hand_results.pkl", help="results store -- accumulates across runs, pass the SAME path to batch")
    parser.add_argument("--out_html", default="hand_visualization.html")
    parser.add_argument("--output_folder", default="output")
    parser.add_argument("--save_crops", action="store_true", help="also write crop jpgs and a comparison overlay to --output_folder")
    args = parser.parse_args()

    image_tag = os.path.splitext(os.path.basename(args.image))[0]

    # Detect + crop every hand in this image (in memory).
    cropper = HandCropper(args.yolo_model, img_output_size=args.crop_size)
    hand_crops = cropper.process(
        args.image, save_to_disk=args.save_crops, output_folder=args.output_folder,
        save_comparison=args.save_crops,
    )
    if not hand_crops:
        print("No hands found -- nothing to infer.")
        return

    # Run HandNet on every crop
    inferencer = HandNetInferencer(args.handnet_model, image_size=args.crop_size, root_index=args.root_index)
    new_results = inferencer.infer_batch(
        crops_rgb=[hc.crop_rgb for hc in hand_crops],
        hand_ids=[f"{image_tag}_hand{hc.hand_index}" for hc in hand_crops],
        source_images=[hc.source_image for hc in hand_crops],
        crop_bounds_list=[hc.crop_bounds for hc in hand_crops],
    )

    # Merge into the results store (accumulates across separate runs).
    all_results = save_results(new_results, args.results, merge=True)
    print(f"Results store '{args.results}' now has {len(all_results)} hand(s): {list(all_results.keys())}")

    # Build ONE interactive HTML covering every hand in the store.
    mano_faces = HandVisualizer.load_mano_faces(args.mano_pkl) if args.mano_pkl else None
    HandVisualizer(mano_faces=mano_faces).add_results(list(all_results.values())).save_html(args.out_html)


if __name__ == "__main__":
    main()
