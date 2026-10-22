import csv
import json
from pathlib import Path

DEFAULT_GROUPS = ["left", "right", "trig_L", "trig_R"]


def find_clips(root):
    """Every clip_XXXX.mp4 under root (a recordings folder, a session folder or one clip)."""
    root = Path(root)
    if root.is_file():
        return [root]

    clips = []
    for video in sorted(root.rglob("clip_*.mp4")):
        if not video.stem.endswith("_overlay"):
            clips.append(video)
    return clips


class ClipFiles:
    """Labels saved by the collector next to a clip video:
        clip_XXXX_frames.csv  rows with the frame time "t" and one label column per group
        clip_XXXX.json        metadata, with the label groups
    """

    def __init__(self, video):
        self.video = Path(video)
        stem = self.video.with_suffix("")
        self.frames_csv = Path(f"{stem}_frames.csv")
        self.meta_path = Path(f"{stem}.json")

        self.rows = []
        self.meta = {}
        self.groups = []

    def load(self):
        """Reads the frame labels and metadata, returns False if the frames csv is missing."""
        if not self.frames_csv.exists():
            return False

        with open(self.frames_csv, newline="") as f:
            self.rows = list(csv.DictReader(f))
        if self.meta_path.exists():
            self.meta = json.loads(self.meta_path.read_text())
        self.groups = self._label_groups()
        return True

    def _label_groups(self):
        if self.meta.get("label_groups"):
            return self.meta["label_groups"]

        # Older clips: groups from the mapping, or the known group columns
        inputs = self.meta.get("mapping", {}).get("inputs", {})
        groups = []
        for spec in inputs.values():
            if "group" in spec and spec["group"] not in groups:
                groups.append(spec["group"])
        if groups:
            return groups

        if not self.rows:
            return []
        return [group for group in DEFAULT_GROUPS if group in self.rows[0]]

    def frame_time(self, idx, fps):
        """Time since the clip start of a frame, from the csv (or fps for extra frames)."""
        if idx < len(self.rows):
            return float(self.rows[idx]["t"])
        return idx / fps

    def frame_labels(self, idx):
        """Group labels of a frame, empty for frames missing in the csv."""
        if idx < len(self.rows):
            return {group: self.rows[idx][group] for group in self.groups}
        return {}
