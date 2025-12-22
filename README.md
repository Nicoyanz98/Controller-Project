# Input Mapper
## Setup
Setup virtual enviroment
```bash
$ python3 -m venv <venv_dir>
```

Activate virtual enviroment
```bash
$ source <venv_dir>/bin/activate
```

Install the requirements:
```bash
$ pip install -r requirements.txt
```
## How to use?
### CaptureHands2
Run the next code to use the data collection tool:
```bash
$ cd capture_hands2
$ python3 main_menu.py
```

### Visualization
Run the next code to use the YOLO Detection visualizator:
```bash
$ cd hand_viz
$ python3 visualization.py
```

## TODO
- [x] Solve problems with event flooding
- [x] Train YOLO Pose for hand keypoint
- [x] Train YOLO for controller zones
- [ ] Solve compatibility for data collection
- [ ] Retrain controller zone detector with more variety
- [ ] Solve overfitting hand keypoint detection
