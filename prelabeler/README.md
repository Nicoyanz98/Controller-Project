# Prelabeler script

Pre-labels the clips recorded by the collector: YOLO controller zones, MediaPipe hand landmarks (smoothed with a One Euro filter) and hand segmentation, per frame. It runs separately from the collector, after the recording.

## Setup

### Creating virtual enviroment
```bash
python -m venv .prelabeler
```
`.prelabeler` can be changed to a custom directory

### Opening virtual enviroment
#### Windows
```bash
.prelabeler\Scripts\activate
```
#### Linux
```bash
source .prelabeler/bin/activate
```

### Installing dependencies
```bash
pip install -r requirements.txt
```

## How to use?
```bash
python prelabel.py 
    --root <data_dir>                   # collector `data_dir`, one session folder or one `clip_XXXX.mp4`
    --yolo <weights.pt>                 # YOLO weights of the zone detector
    --hand_model <hand_landmarker.task> # MediaPipe
    [--out <prelabels_dir>]             # saved in `<prelabels_dir>/<session>/`. By default they are saved next to each clip
    [--overlay]                         # writes `clip_XXXX_overlay.mp4` with the detections drawn
```

Clips with outputs are skipped, add `--overwrite` to process them again. Run `python prelabel.py --help` for the YOLO, MediaPipe, filter and segmentation settings (`--seg skin` by default, `--seg none` to skip it) or go to the section [Other parameters](#other-parameters).

## Output
Per clip:
- `clip_0001_pre.npz`: per frame zone boxes, hand landmarks (raw and filtered), hand slots, zone coverage by the hands and the group labels of the clip.
- `clip_0001_masks.npz`: downscaled hand part masks (only with segmentation).
- `clip_0001_overlay.mp4`: with `--overlay`.

And per session `prelabel_summary.csv`, with the hand and zone detection rates of each clip.

The outputs are the same as `video_analysis/prelabel.py`, so they can be analyzed with `video_analysis/analyze.py --prelabels <prelabels_dir>`.

## Other parameters
### YOLO
```bash
python prelabel.py 
    --imgsz <img_size> 
    --conf <confidence> 
    --device <device_id> 
    --batch <size>
```
### MediaPipe
```bash
python prelabel.py 
    --det_conf <detection_confidence> 
    --press_conf <pressing_confidence> 
    --track_conf <tracking_confidence> 
    --hand_slot <slot_method>
```

### One Euro filter
```bash
python prelabel.py  
    --min_cuttof <cutoff_value> 
    --beta <beta_value> 
    --d_cuttoff <d_cuttoff_value>
    --max_jump <threshold>
    --world_beta <world_beta_value>
    [--no_filter]
    [--filter_world]
```

### Segmentation
```bash
python prelabel.py 
    --seg <segmentation_type> 
    --std_factor <color_tolerance> 
    --seg_width_scale <finger_multiplier>
    --palm_expand <palm_value>
    --tip_extend <tip_value>
    --mask_width <width>
    [--robut_skin]
```

## Modules
- `prelabel.py`: command line and the loop over the clips.
- `clip_prelabeler.py`: processing of one clip, frame by frame.
- `clip_files.py`: finds the clips and reads the collector labels (`_frames.csv`, `.json`).
- `detectors.py`: YOLO zones and MediaPipe hands.
- `hand_slots.py`: keeps each hand in the same slot (0/1) across frames.
- `landmark_filter.py`: One Euro filter of the landmarks.
- `hand_segmentation.py`: skin and landmark based hand segmentation, split into hand parts.
- `zones.py`: best box per zone and zone coverage by the hands.
- `overlay.py`: overlay video.
- `prelabel_results.py`: per frame results and the saved npz files.
