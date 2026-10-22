import os

# Hide warnings
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import csv
import argparse

from clip_files import find_clips
from clip_prelabeler import ClipPrelabeler
from detectors import YoloZones, MediaPipeHands
from hand_segmentation import load_segmentation


class Prelabeler:
    """Pre-labels the clips recorded by the collector with YOLO zones and MediaPipe hands,
    and writes a prelabel_summary.csv per session."""

    def __init__(self, root, clip_prelabeler):
        self.root = root
        self.clip_prelabeler = clip_prelabeler

    def run(self):
        clips = find_clips(self.root)
        if not clips:
            raise SystemExit(f"No clip_*.mp4 found under {self.root}")

        stats_by_session = {}
        try:
            for count, video in enumerate(clips, 1):
                stats, status = self.clip_prelabeler.process(video)
                if stats is None:
                    print(f"[{count}/{len(clips)}] {video}: skipped ({status})")
                    continue

                warning = "  (frame count differs from csv)" if stats["csv_mismatch"] else ""
                print(f"[{count}/{len(clips)}] {video}: {stats['n_frames']} frames, "
                      f"hands {stats['hand0_rate']:.0%}/{stats['hand1_rate']:.0%}, "
                      f"{stats['fps_processed']} fps{warning}")
                session = self.clip_prelabeler.output_dir(video)
                stats_by_session.setdefault(session, []).append(stats)
        finally:
            self.clip_prelabeler.hands.close()

        for session, session_stats in stats_by_session.items():
            self._write_summary(session / "prelabel_summary.csv", session_stats)

    def _write_summary(self, path, session_stats):
        """Updates the summary of a session, keeping the rows of clips processed before."""
        rows = {}
        if path.exists():
            with open(path, newline="") as f:
                for row in csv.DictReader(f):
                    rows[row["clip"]] = row
        for stats in session_stats:
            rows[stats["clip"]] = stats

        fieldnames = []
        for row in rows.values():
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)

        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for clip in sorted(rows):
                writer.writerow(rows[clip])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-labels collector clips with YOLO zones and MediaPipe hands.")
    parser.add_argument("--root", required=True, help="Collector data folder, a session folder or one clip .mp4")
    parser.add_argument("--yolo", required=True, help="YOLO weights (.pt) of the zone detector")
    parser.add_argument("--hand_model", required=True, help="MediaPipe hand_landmarker.task")
    parser.add_argument("--out", help="Folder for the outputs, mirrored as <out>/<session>/ (default: next to each clip)")
    parser.add_argument("--overlay", action="store_true", help="Write clip_XXXX_overlay.mp4 for visual QA")
    parser.add_argument("--overwrite", action="store_true", help="Process again clips that already have outputs")

    yolo_args = parser.add_argument_group("YOLO")
    yolo_args.add_argument("--imgsz", type=int, default=640)
    yolo_args.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    yolo_args.add_argument("--device", help="Device, e.g. 0, cpu, mps")
    yolo_args.add_argument("--batch", type=int, default=16, help="Frames per batch")

    hand_args = parser.add_argument_group("MediaPipe hands")
    hand_args.add_argument("--det_conf", type=float, default=0.5)
    hand_args.add_argument("--pres_conf", type=float, default=0.5)
    hand_args.add_argument("--track_conf", type=float, default=0.5)
    hand_args.add_argument("--hand_slot", default="image_x", choices=["image_x", "mediapipe", "mediapipe_swapped"], help="How hands are assigned to slot 0/1, keep it fixed for the whole dataset")

    filter_args = parser.add_argument_group("One Euro filter (landmarks)")
    filter_args.add_argument("--no_filter", dest="filter", action="store_false")
    filter_args.add_argument("--min_cutoff", type=float, default=2.5, help="Increase if laggy, decrease if jittery at rest")
    filter_args.add_argument("--beta", type=float, default=1.5, help="Increase to reduce lag in fast movements")
    filter_args.add_argument("--d_cutoff", type=float, default=1.0)
    filter_args.add_argument("--max_jump", type=float, default=0.25, help="Restart a slot filter if its wrist jumps more than this (normalized units)")
    filter_args.add_argument("--filter_world", action="store_true", help="Also filter the world landmarks")
    filter_args.add_argument("--world_beta", type=float, default=1.5, help="Beta of the world landmarks filter")

    seg_args = parser.add_argument_group("Segmentation")
    seg_args.add_argument("--seg", default="skin", help="'skin', 'none' or module.path:function")
    seg_args.add_argument("--std_factor", type=float, default=2.0, help="Skin: colour tolerance in std units")
    seg_args.add_argument("--robust_skin", action="store_true", help="Skin: median/MAD colour stats (less pulled by controller pixels)")
    seg_args.add_argument("--seg_width_scale", type=float, default=1.0, help="Finger width multiplier of the part labels")
    seg_args.add_argument("--palm_expand", type=float, default=1.15)
    seg_args.add_argument("--tip_extend", type=float, default=0.25)
    seg_args.add_argument("--mask_width", type=int, default=160, help="Saved mask width (height keeps aspect)")

    args = parser.parse_args()

    image_filter = {
        "min_cutoff": args.min_cutoff,
        "beta": args.beta,
        "d_cutoff": args.d_cutoff,
        "enabled": args.filter,
        "max_jump": args.max_jump,
    }
    world_filter = {
        "min_cutoff": args.min_cutoff,
        "beta": args.world_beta,
        "d_cutoff": args.d_cutoff,
        "enabled": args.filter and args.filter_world,
    }

    zones = YoloZones(args.yolo, args.imgsz, args.conf, args.device, args.batch)
    hands = MediaPipeHands(args.hand_model, 2, args.det_conf, args.pres_conf, args.track_conf)
    segmentation = load_segmentation(args.seg, args.std_factor, args.robust_skin, args.seg_width_scale, args.palm_expand, args.tip_extend)

    clip_prelabeler = ClipPrelabeler(zones, hands, segmentation, args.out, args.hand_slot, image_filter, world_filter, args.mask_width, args.overlay, args.overwrite)
    prelabeler = Prelabeler(args.root, clip_prelabeler)
    prelabeler.run()
