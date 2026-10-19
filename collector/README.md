# Collector script

## Setup

### Creating virtual enviroment
```bash
python -m venv .collector
```
`.collector` can be changed to a custom directory

### Opening virtual enviroment
#### Windows
```bash
.collector\Scripts\activate
```
#### Linux
```bash
source .collector/bin/activate
```

### Installing dependencies
```bash
pip install -r requirements.txt
```

## Running
```bash
python collector.py --save_dir <data_dir> --t_no_input <seconds> --t_tail <seconds> --t_continue <seconds> --t_max <seconds> --fps <fps> [--mjpg]
```
`data_dir` will hold every clip obtained. By default its created on `./data`.

Using `--mjpg` is recommended to increase fps of the clip.

### Recording clips
1. Press **Start** or **Select** to start recording.
2. Use the controller. A clip ends `t_tail` seconds (default 0.5) after every input is released, and is saved.
3. Recording continues after each saved clip: any input within `t_continue` seconds (default 1.5) starts filling a new clip, so there is no need to press Start/Select again.
4. Recording stops when no input arrives in time (`t_no_input`, default 2.0, after Start/Select; `t_continue` after a saved clip) or when Start/Select is pressed again.

`fps` (default 30) is the frame rate requested to the camera. For higher values (e.g. 60) add `--mjpg`, since many cameras only reach them with MJPG. The real fps is measured at launch and a warning is shown if it differs from the requested one.

Clips longer than `t_max` seconds (default 10) are split. Press `q` in the preview window to quit (a clip in progress is discarded).

### Output
Clips will be saved in numbered directories (0, 1, 2, etc), for each time it was executed on the same directory:
- `clip_0001.mp4`: raw camera frames.
- `clip_0001_labels.csv`: one row per frame with its time since the clip start and the pressed inputs label (`basura` when idle).
 
## Sending images
Zip `data_dir` with 7-zip as `.7z` file and upload it to the Google Drive URL provided by the author.