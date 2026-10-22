import numpy as np

N_LANDMARKS = 21


class YoloZones:
    """YOLO detector of the controller zones, run on batches of frames."""

    def __init__(self, weights, imgsz=640, conf=0.25, device=None, batch=16):
        from ultralytics import YOLO

        self.model = YOLO(weights)
        self.names = [self.model.names[idx] for idx in sorted(self.model.names)]
        self.batch = batch

        self.options = {"imgsz": imgsz, "conf": conf, "verbose": False}
        if device is not None:
            self.options["device"] = device

        self.desc = {"yolo_weights": str(weights), "imgsz": imgsz, "conf": conf}
        if device is not None:
            self.desc["device"] = device

    def detect(self, frames):
        """Returns per BGR frame a (k, 6) array of boxes: x1, y1, x2, y2, conf, cls."""
        detections = []
        for result in self.model.track(frames, **self.options, tracker="bytetrack.yaml"):
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                detections.append(np.zeros((0, 6), np.float32))
                continue

            xyxy = boxes.xyxy.cpu().numpy()
            conf = boxes.conf.cpu().numpy()[:, None]
            cls = boxes.cls.cpu().numpy()[:, None]
            detections.append(np.concatenate([xyxy, conf, cls], 1).astype(np.float32))
        return detections


class MediaPipeHands:
    """MediaPipe hand landmarker in video mode, restarted for every clip."""

    def __init__(self, model_path, num_hands=2, det_conf=0.5, pres_conf=0.5, track_conf=0.5):
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision

        self.mp = mp
        self.vision = vision
        self.options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=det_conf,
            min_hand_presence_confidence=pres_conf,
            min_tracking_confidence=track_conf,
        )
        self.landmarker = None

        self.desc = {
            "hand_model": str(model_path),
            "num_hands": num_hands,
            "det_conf": det_conf,
            "pres_conf": pres_conf,
            "track_conf": track_conf,
        }

    def start_clip(self):
        """Video mode needs increasing timestamps, a new landmarker per clip resets the tracking."""
        self.close()
        self.landmarker = self.vision.HandLandmarker.create_from_options(self.options)

    def detect(self, frame_rgb, timestamp_ms):
        """Returns a list of hands: {img (21, 3), world (21, 3), label 0 Left / 1 Right / -1, score}."""
        image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(frame_rgb))
        result = self.landmarker.detect_for_video(image, int(timestamp_ms))

        hands = []
        for idx, landmarks in enumerate(result.hand_landmarks):
            hand = {
                "img": np.array([[point.x, point.y, point.z] for point in landmarks], np.float32),
                "world": np.full((N_LANDMARKS, 3), np.nan, np.float32),
                "label": -1,
                "score": 0.0,
            }

            if idx < len(result.hand_world_landmarks):
                world_landmarks = result.hand_world_landmarks[idx]
                hand["world"] = np.array([[point.x, point.y, point.z] for point in world_landmarks], np.float32)

            if idx < len(result.handedness) and result.handedness[idx]:
                category = result.handedness[idx][0]
                hand["label"] = 0 if category.category_name.lower() == "left" else 1
                hand["score"] = float(category.score)

            hands.append(hand)
        return hands

    def close(self):
        if self.landmarker is not None:
            self.landmarker.close()
            self.landmarker = None
