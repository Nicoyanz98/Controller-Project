# Input Mapper
## Setup

### Creating virtual enviroment
```bash
python -m venv .input_mapper
```
`.input_mapper` can be changed to a custom directory

### Opening virtual enviroment
#### Windows
```bash
.input_mapper\Scripts\activate
```
#### Linux
```bash
source .input_mapper/bin/activate
```

### Installing dependencies
```bash
pip install -r requirements.txt
```

## Collector Usage
```bash
$ cd collector
$ python collector.py 
    --save_dir <data_dir>   # holds every clip obtained. By default created on ./data
    --subject <id>          # by default s00 to identify person recorded
    --t_no_input <seconds>  # seconds before the clip stops after no input is pressed. By default 2s
    --t_tail <seconds>      # seconds after input before the clip stops. By default 0.5s
    --t_continue <seconds>  # seconds before starting a new clip after one was saved. By default 1.5s
    --t_max <seconds>       # max duration of a clip. By default 10s
    --fps <fps>             # by default 30
    [--mjpg]                # recommended to match fps required of the clip
```

### How to record clips?
1. Press **Start** or **Select** to start recording.
2. Use the controller. A clip ends `t_tail` seconds (default 0.5) after every input is released, and is saved.
3. Recording continues after each saved clip after `t_continue` seconds (default 1.5), so there is no need to press Start/Select again.
4. Recording stops when after `t_no_input` (default 2.0) seconds no input arrives in time or when Start/Select is pressed again.

`fps` (default 30) is the frame rate requested to the camera. For higher values (e.g. 60) add `--mjpg`, since many cameras only reach them with MJPG. The real fps is measured at launch and a warning is shown if it differs from the requested one.

Clips longer than `t_max` seconds (default 10) are split. Press `q` in the preview window to quit (a clip in progress is discarded).

### Collector Output
Each run creates a session folder `<data_dir>/<subject>_<YYYYmmdd-HHMMSS>/`:
- `clip_0001.mp4`: raw camera frames.
- `clip_0001_frames.csv`: one row per frame with `t` (seconds since the clip start), one label column per group (`left`, `right`, `trig_L`, `trig_R`), 0/1 per input and the raw axis values (-1..1, triggers 0..1).
- `clip_0001_events.csv`: press / release of every input, with `t` since the clip start.
- `clip_0001.json`: metadata (fps, resolution, timings, pressed inputs, label groups, ...).
- `index.csv`: one row per saved clip of the session.

Group labels are `none`, the pressed input (e.g. `a`, `ls_up`, `rt`) or `conflict:a+b` when two inputs of the same group are pressed together. Inputs use SDL names on every controller. Sticks and dpad have 8 directions: diagonals are their own input (`ls_up_left`, `dpad_down_right`, ...), a stick direction is pressed when its axis passes half of its range.

## Sending images
Zip `data_dir` with 7-zip as `.7z` file and upload it to the Google Drive URL provided by the author.

### Visualization
Run the next code to use the YOLO Detection visualizator:
```bash
$ cd visualization
$ python3 run_detector.py 
    --hand_model <mediapipe_hand_landmark.task>
    --joystick_model <joystick_yolo_model.pt>
```

## TODO
- [x] Solve problems with event flooding
- [x] ~~Train YOLO Pose for hand keypoint~~
- [x] Train YOLO for controller zones
- [x] Retrain controller zone detector with more variety
- [ ] Collect video clip samples from various subjects (~160 currently from 1 subject)
- [ ] Generate dataset (hand and zone annotations from trained models)
- [ ] Train network 
- [ ] Run test on video clips
- [ ] Real time testing
