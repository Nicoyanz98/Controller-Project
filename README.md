# ReJSHand Tester
## Hand Cropper
Allows for cropping hands from images using YOLO 26 Hand pose [pretrained model]((https://huggingface.co/poptoz/yolo26-hand-pose-face-detection))

```bash
python hand_cropper.py --model ./models/yolo26_hand_pose.pt --image ./img/<img_path> --image_size 224 --output_folder ./output
```

## Interactive Visualizer
Visualizer for ReJSHand hand pose net with a pretrained model (use original repo for trainin and export model as `.pt` file).

```bash
python visualize_inference.py --model ./models/rejshand_net.pt --image ./img/<img_path> --mano_pkl ./mano_models/MANO_LEFT_C.pkl
```

## TODO
- [x] Inference without custom HandNet class
- [x] Show 3D Mesh inference with manual rotation
- [x] Crop hands in an image to feed the HandNet
- [x] Infer every hand from an image after cropping them
- [ ] Real-time
    - [ ] Connect to livefeed from webcam and infer every few seconds
    - [ ] Mantain rotations for each hand between new frames (and runs)
    - [ ] Paralelize inferences to increase framerate (if necessary)
- [ ] Inetegrate Joystick RoI model

## Bugs found
- **One 2D keypoint of index finger seems to be "fixed" to a specific direction however the 3D Mesh doesn't show this.**
    - Changing root index doesn't change behaviour
    - Possible coordinates errors if the keypoints is 9 (training root index problem)
        *Confirmed that keypoint 8 (9th counting from 0) is the offset keypoint*
	
- **3D Mesh seems to be always right handed even for left hands.** 
    - Need to check horizontal flip of 3D Mesh to see if problem is in the visualization and not the result
	- 2D keypoints seem to replicate behaviour
        *Can't verify this because joints coordinates are scaled while UV pixels aren't*
	- See if image mirroring would be necessary for correct predictions 
        *Will need to account for handedness detection to work*
        *Test mediapipe handedness detection with pretrained model*
    - HandNet training suggest that right handed is canonically the mesh handedness because of a Random Flip used 
    *Further investigation to find if removing it should solve the handedness or decrease accuracy*