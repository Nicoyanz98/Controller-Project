import time
from pathlib import Path

import cv2
import numpy as np

from clip_files import ClipFiles
from detectors import N_LANDMARKS
from hand_segmentation import N_PARTS, to_slot_parts
from hand_slots import N_SLOTS, SlotAssigner
from landmark_filter import LandmarkFilterBank
from overlay import OverlayWriter
from prelabel_results import PrelabelResults
from zones import best_per_class, zone_coverage


class FrameHands:
    """Hands of one frame, one entry per slot (NaN landmarks when the slot is empty)."""

    def __init__(self):
        self.present = np.zeros(N_SLOTS, bool)
        self.landmarks_img_raw = np.full((N_SLOTS, N_LANDMARKS, 3), np.nan, np.float32)
        self.landmarks_world_raw = np.full((N_SLOTS, N_LANDMARKS, 3), np.nan, np.float32)
        self.score = np.zeros(N_SLOTS, np.float32)
        self.handedness = np.full(N_SLOTS, -1, np.int8)

        # Filtered landmarks
        self.landmarks_img = self.landmarks_img_raw.copy()
        self.landmarks_world = self.landmarks_world_raw.copy()

    def set_hand(self, slot, hand):
        self.present[slot] = True
        self.landmarks_img_raw[slot] = hand["img"]
        self.landmarks_world_raw[slot] = hand["world"]
        self.score[slot] = hand["score"]
        self.handedness[slot] = hand["label"]

    def present_slots(self):
        return [slot for slot in range(N_SLOTS) if self.present[slot]]


class ClipPrelabeler:
    """Runs the zone detector, hand landmarks, landmark filter and hand segmentation
    over every frame of a clip and saves clip_XXXX_pre.npz (see PrelabelResults).

        out_dir        folder for the outputs, mirrored as <out_dir>/<session>/ (None: next to each clip)
        hand_slot      SlotAssigner mode
        image_filter   LandmarkFilterBank params for the image landmarks
        world_filter   LandmarkFilterBank params for the world landmarks
        mask_width     width of the saved masks (height keeps aspect)
        overlay        also writes clip_XXXX_overlay.mp4
        overwrite      re-process clips that already have a clip_XXXX_pre.npz
    """

    def __init__(self, zones, hands, segmentation, out_dir, hand_slot, image_filter, world_filter, mask_width, overlay, overwrite):
        self.zones = zones
        self.hands = hands
        self.segmentation = segmentation

        self.out_dir = out_dir
        self.hand_slot = hand_slot
        self.image_filter = image_filter
        self.world_filter = world_filter
        self.mask_width = mask_width
        self.overlay = overlay
        self.overwrite = overwrite

    def output_dir(self, video):
        """Where the outputs of a clip go: <out_dir>/<session>/ or next to the clip."""
        if self.out_dir:
            return Path(self.out_dir) / video.parent.name
        return video.parent

    def process(self, video):
        """Pre-labels one clip. Returns (stats, status), stats is None when the clip is skipped."""
        out_dir = self.output_dir(video)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_stem = out_dir / video.stem
        out_path = Path(f"{out_stem}_pre.npz")
        if out_path.exists() and not self.overwrite:
            return None, "exists"

        clip = ClipFiles(video)
        if not clip.load():
            return None, "no frames csv"

        cap = cv2.VideoCapture(str(video))
        if not cap.isOpened():
            return None, "cannot open video"
        fps = cap.get(cv2.CAP_PROP_FPS) or clip.meta.get("fps_measured") or 30.0
        n_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self._start_clip(clip, fps, out_stem)
        t_start = time.perf_counter()
        for batch in _read_batches(cap, self.zones.batch):
            detections = self.zones.detect(batch)
            for frame, frame_detections in zip(batch, detections):
                self._process_frame(frame, frame_detections)
        cap.release()
        if self.overlay_writer is not None:
            self.overlay_writer.close()

        n_frames = len(self.results)
        if n_frames == 0:
            return None, "no frames decoded"

        labels = {}
        for group in clip.groups:
            labels[group] = [clip.frame_labels(idx).get(group, "") for idx in range(n_frames)]

        meta = {
            "script": "prelabeler/prelabel.py",
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "source_video": str(video.resolve()),
            "source_frames_csv": str(clip.frames_csv.resolve()),
            "session": video.parent.name,
            "hand_slot": self.hand_slot,
            "mask_width": self.mask_width if self.segmentation else None,
            "filter_img": self.landmark_filter_img.params(),
            "filter_world": self.landmark_filter_world.params(),
            "segmentation": getattr(self.segmentation, "desc", None) if self.segmentation else None,
            "fps": fps,
            "n_frames_video_header": n_video_frames,
            "n_frames_decoded": n_frames,
            "n_frames_csv": len(clip.rows),
            **self.zones.desc,
            **self.hands.desc,
        }
        self.results.save(out_path, self.image_size, self.zones.names, labels, meta)
        self.results.save_masks(f"{out_stem}_masks.npz")

        stats = {
            "clip": video.stem,
            "n_frames": n_frames,
            "csv_mismatch": int(n_frames != len(clip.rows)),
            **self.results.stats(self.zones.names),
            "fps_processed": round(n_frames / (time.perf_counter() - t_start), 1),
        }
        return stats, "ok"

    def _start_clip(self, clip, fps, out_stem):
        """Resets the per clip state: tracking, filters and results."""
        self.clip = clip
        self.fps = fps
        self.frame_idx = 0
        self.last_timestamp_ms = -1
        self.image_size = None

        self.hands.start_clip()
        self.slots = SlotAssigner(self.hand_slot)
        self.landmark_filter_img = LandmarkFilterBank(**self.image_filter)
        self.landmark_filter_world = LandmarkFilterBank(**self.world_filter)
        self.results = PrelabelResults()

        self.overlay_writer = None
        if self.overlay:
            self.overlay_writer = OverlayWriter(f"{out_stem}_overlay.mp4", fps)

    def _process_frame(self, frame, detections):
        h, w = frame.shape[:2]
        self.image_size = (w, h)
        idx = self.frame_idx
        t = self.clip.frame_time(idx, self.fps)

        # MediaPipe video mode needs strictly increasing timestamps
        timestamp_ms = max(int(round(t * 1000)), self.last_timestamp_ms + 1)
        self.last_timestamp_ms = timestamp_ms
        detected_hands = self.hands.detect(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), timestamp_ms)

        hands = FrameHands()
        for slot, hand in self.slots.assign(detected_hands):
            hands.set_hand(slot, hand)
        self._filter_landmarks(hands, t)

        xyxy, conf = best_per_class(detections, len(self.zones.names))
        coverage = np.full(len(self.zones.names), np.nan, np.float32)
        part_coverage = np.full((len(self.zones.names), N_SLOTS, N_PARTS), np.nan, np.float32)
        masks = None
        if self.segmentation is not None:
            # Segments the filtered landmarks
            masks = to_slot_parts(self.segmentation(frame, hands.landmarks_img, hands.present), h, w)
            coverage, part_coverage = zone_coverage(masks, xyxy, conf > 0)
            self.results.add_masks(self._resize_masks(masks, h, w))

        raw_boxes = np.zeros((0, 7), np.float32)
        if len(detections):
            frame_column = np.full((len(detections), 1), idx, np.float32)
            raw_boxes = np.concatenate([frame_column, detections], 1)
        self.results.add_frame(t, (xyxy, conf, coverage, part_coverage), hands, raw_boxes)

        if self.overlay_writer is not None:
            self.overlay_writer.write(frame, xyxy, conf, self.zones.names, hands.landmarks_img, hands.present, masks, self.clip.frame_labels(idx))
        self.frame_idx += 1

    def _filter_landmarks(self, hands, t):
        """One Euro filter per slot, the filters of missing hands are dropped."""
        present_slots = hands.present_slots()
        for slot in present_slots:
            hands.landmarks_img[slot] = self.landmark_filter_img.apply(slot, hands.landmarks_img_raw[slot], t)
            hands.landmarks_world[slot] = self.landmark_filter_world.apply(slot, hands.landmarks_world_raw[slot], t)
        self.landmark_filter_img.keep_only(present_slots)
        self.landmark_filter_world.keep_only(present_slots)

    def _resize_masks(self, masks, h, w):
        mask_height = max(int(round(h * self.mask_width / w)), 1)
        resized = []
        for slot in range(N_SLOTS):
            resized.append(cv2.resize(masks[slot], (self.mask_width, mask_height), interpolation=cv2.INTER_NEAREST))
        return np.stack(resized)


def _read_batches(cap, batch_size):
    """Yields the video frames in lists of batch_size."""
    batch = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        batch.append(frame)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
